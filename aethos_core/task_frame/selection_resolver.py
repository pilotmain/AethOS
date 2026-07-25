# SPDX-License-Identifier: Apache-2.0
"""Selection resolver — map user reply to pending candidate."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.task_frame.task_frame import TaskCandidate, TaskFrame

_INDEX_ONLY_RX = re.compile(r"^\s*(\d+)\.?\s*$")
_INDEX_WITH_PATH_RX = re.compile(r"^\s*(\d+)\.\s*(.+?)\s*$")
_MULTI_INDEX_RX = re.compile(r"\b(\d+(?:\s*,\s*|\s+and\s+)\d+)\b", re.I)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def resolve_selection(text: str, frame: TaskFrame) -> TaskCandidate | None:
    selected = resolve_selections(text, frame)
    if not selected:
        return None
    return selected[0]


def resolve_selections(text: str, frame: TaskFrame) -> list[TaskCandidate]:
    raw = (text or "").strip()
    if not raw or not frame.candidates:
        return []

    index_match = _INDEX_ONLY_RX.match(raw)
    if index_match:
        candidate = _candidate_by_index(int(index_match.group(1)), frame.candidates)
        return [candidate] if candidate is not None else []

    indexed_path = _INDEX_WITH_PATH_RX.match(raw)
    if indexed_path:
        candidate = _candidate_by_index(int(indexed_path.group(1)), frame.candidates)
        if candidate is None:
            return []
        path_text = indexed_path.group(2).strip()
        if _path_matches_candidate(path_text, candidate):
            return [candidate]
        return []

    multi = _MULTI_INDEX_RX.search(raw)
    if multi:
        indices = [int(token) for token in re.findall(r"\d+", multi.group(1))]
        selected = [_candidate_by_index(index, frame.candidates) for index in indices]
        return [row for row in selected if row is not None]

    from aethos_core.providers.railway.railway_inventory_target_picker import (
        looks_like_target_selection_reply,
        parse_target_selection_reply,
    )

    env_hint, service_tokens = parse_target_selection_reply(raw)
    if service_tokens and (
        env_hint
        or looks_like_target_selection_reply(raw)
        or len(service_tokens) > 1
    ):
        matched = _match_service_tokens(service_tokens, frame.candidates, environment_hint=env_hint)
        if matched:
            return matched

    norm = _normalize(raw)
    matched: list[TaskCandidate] = []
    for candidate in frame.candidates:
        if _path_matches_candidate(raw, candidate):
            matched.append(candidate)
        elif norm == _normalize(candidate.service):
            matched.append(candidate)
        elif norm == _normalize(candidate.path or ""):
            matched.append(candidate)
    if matched:
        return _dedupe_candidates(matched)
    return []


def _match_service_tokens(
    tokens: list[str],
    candidates: list[TaskCandidate],
    *,
    environment_hint: str = "",
) -> list[TaskCandidate]:
    matched: list[TaskCandidate] = []
    env = (environment_hint or "").lower()
    for token in tokens:
        norm = _normalize(token)
        for candidate in candidates:
            if env and _normalize(candidate.environment) != env:
                continue
            if _service_matches_token(candidate.service, norm, path=_normalize(candidate.path or "")):
                matched.append(candidate)
                break
    return _dedupe_candidates(matched)


def _service_matches_token(service: str, token: str, *, path: str = "") -> bool:
    svc = _normalize(service)
    if svc == token:
        return True
    if "-" in token and "." not in token:
        return svc == token
    if token in svc or svc in token or token in path:
        return True
    return False


def _dedupe_candidates(candidates: list[TaskCandidate]) -> list[TaskCandidate]:
    out: list[TaskCandidate] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = candidate.path or f"{candidate.project}:{candidate.environment}:{candidate.service}"
        if key in seen:
            continue
        seen.add(key)
        out.append(candidate)
    return out


def _candidate_by_index(index: int, candidates: list[TaskCandidate]) -> TaskCandidate | None:
    for candidate in candidates:
        if candidate.index == index:
            return candidate
    return None


def _path_matches_candidate(text: str, candidate: TaskCandidate) -> bool:
    norm = _normalize(text)
    path = _normalize(candidate.path or "")
    if not path:
        return False
    if norm == path:
        return True
    if path in norm or norm in path:
        return True
    triple = _normalize(f"{candidate.project} / {candidate.environment} / {candidate.service}")
    return norm == triple or triple in norm or norm in triple


def selection_error_message(frame: TaskFrame) -> str:
    lines = [f"{c.index}. {c.path or c.service}" for c in frame.candidates[:8]]
    op = frame.operation.replace("_", " ")
    return (
        f"I couldn't match that to a Railway target for **{op}**.\n\n"
        "Reply with the option number, full path, or environment + services, for example:\n"
        "- `staging: aethos-api, aethos-ui`\n"
        + "\n".join(lines[:4])
        + "\n\nNo mutation preflight has been created yet."
    )
