# SPDX-License-Identifier: Apache-2.0
"""Resolve explicit failed-service targets from user text and health report."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

from aethos_core.failed_service_investigation.failed_service_memory import (
    get_failed_health_rows,
    get_health_report_rows,
    row_key,
)
from aethos_core.response_composition.render_pipeline.filter_engine import is_failed_row

InvestigationKind = Literal["why_failed", "fix_plan", "check_logs", "inspect_events", "status", "none"]


@dataclass
class ResolvedFailedService:
    row: dict[str, Any]
    provider: str = "railway"
    match_reason: str = ""
    investigation_kind: InvestigationKind = "none"


@dataclass
class FailedServiceResolution:
    ok: bool
    kind: InvestigationKind = "none"
    target: ResolvedFailedService | None = None
    candidates: list[dict[str, Any]] | None = None
    reason: str = ""


_WHY_FAILED_RX = re.compile(
    r"\bwhy\s+(?:is|are|did|was)\s+(.+?)\s+(?:fail(?:ed|ing)?|down|crashed|broken)\b",
    re.I,
)
_WHY_FAILED_SHORT_RX = re.compile(r"\bwhy\s+(?:is|did)\s+(.+?)\s+fail\b", re.I)
_FIX_PLAN_RX = re.compile(
    r"\b(?:create|make|build|draft|give\s+me)\s+(?:a\s+)?fix\s+plan\s+(?:for\s+)?(.+?)\s*$",
    re.I,
)
_LOGS_RX = re.compile(
    r"\b(?:check|show|fetch|get|read|tail)\s+(?:the\s+)?logs?\s+(?:for\s+)?(.+?)\s*$",
    re.I,
)
_INVESTIGATION_RX = re.compile(
    r"\b(?:diagnose|investigate|debug|analyze)\s+(?:the\s+)?(.+?)(?:\s+failure|\s+service)?\s*$",
    re.I,
)


def classify_failed_service_investigation(text: str) -> InvestigationKind:
    from aethos_core.failed_service_investigation.global_preemption import (
        _intent_to_kind,
        classify_failed_service_intent,
    )

    return _intent_to_kind(classify_failed_service_intent(text))


def _extract_phrase(text: str, kind: InvestigationKind) -> str:
    from aethos_core.failed_service_investigation.global_preemption import classify_failed_service_intent

    raw = (text or "").strip()
    intent = classify_failed_service_intent(raw)
    for rx in (
        _WHY_FAILED_RX,
        _WHY_FAILED_SHORT_RX,
        _FIX_PLAN_RX,
        _LOGS_RX,
        _INVESTIGATION_RX,
        re.compile(r"\b(?:inspect|check|show|fetch|get|list|read)\s+(?:the\s+)?(.+?\s+)?(?:service\s+)?events?\b", re.I),
        re.compile(r"\b(?:check|show|fetch|get|read|tail)\s+(?:the\s+)?(.+?\s+)?error\s+logs?\b", re.I),
        re.compile(r"\b(?:(?:what(?:'s|\s+is)\s+(?:the\s+)?status(?:\s+(?:of|for))?)|status\s+(?:of|for))\s+(.+?)\s*$", re.I),
    ):
        match = rx.search(raw)
        if match:
            return match.group(1).strip(" .?!")
    return raw


def _normalize_token(value: str) -> str:
    return re.sub(r"[\s_\-]+", " ", (value or "").strip().lower())


def _token_in_text(token: str, text: str) -> bool:
    if not token:
        return False
    raw_lower = (text or "").lower()
    token_lower = token.lower()
    token_norm = _normalize_token(token)
    raw_norm = _normalize_token(text)
    if token_lower in raw_lower:
        return True
    if token_norm and token_norm in raw_norm:
        return True
    if token_lower.replace("-", " ") in raw_lower:
        return True
    return False


def matches_failed_service_from_cache(text: str, *, session_id: str = "default", provider: str = "railway") -> bool:
    rows = get_health_report_rows(session_id=session_id, provider=provider)
    if not rows:
        return False
    for row in rows:
        service = str(row.get("service") or "")
        project = str(row.get("project") or "")
        service_id = str(row.get("service_id") or "")
        combined = f"{project}/{service}".strip("/")
        for candidate in (service, project, service_id, combined):
            if len(candidate) >= 2 and _token_in_text(candidate, text):
                return True
    return False


def _score_row_match(row: dict[str, Any], phrase: str, raw_text: str) -> int:
    service = str(row.get("service") or "")
    project = str(row.get("project") or "")
    environment = str(row.get("environment") or "")
    service_id = str(row.get("service_id") or "")
    phrase_norm = _normalize_token(phrase)
    raw_norm = _normalize_token(raw_text)
    score = 0

    combined = _normalize_token(f"{project} {service}")
    if combined and (combined == phrase_norm or combined in raw_norm or phrase_norm in combined):
        score += 120

    for label in (service, project, environment, service_id):
        token = _normalize_token(label)
        if not token:
            continue
        if token == phrase_norm:
            score += 100
        elif _token_in_text(label, phrase) or _token_in_text(label, raw_text):
            score += 85
        elif token in phrase_norm or phrase_norm in token:
            score += 80
        elif token in raw_norm:
            score += 65

    project_norm = _normalize_token(project)
    service_norm = _normalize_token(service)
    if project_norm and project_norm in raw_norm:
        score += 45
        if service_norm and service_norm in raw_norm:
            score += 35
    if score > 0 and is_failed_row(row):
        score += 10
    return score


def _match_rows(rows: list[dict[str, Any]], phrase: str, raw_text: str) -> list[dict[str, Any]]:
    scored: list[tuple[int, dict[str, Any]]] = []
    for row in rows:
        score = _score_row_match(row, phrase, raw_text)
        if score > 0:
            scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    if not scored:
        return []
    top_score = scored[0][0]
    return [row for score, row in scored if score >= max(top_score - 5, top_score * 0.85)]


def resolve_failed_service_target(
    text: str,
    *,
    session_id: str = "default",
    kind: InvestigationKind | None = None,
    provider: str = "railway",
) -> FailedServiceResolution:
    investigation_kind = kind or classify_failed_service_investigation(text)
    if investigation_kind == "none":
        return FailedServiceResolution(ok=False, kind="none", reason="not_investigation_request")

    rows = get_health_report_rows(session_id=session_id, provider=provider)
    if not rows:
        return FailedServiceResolution(ok=False, kind=investigation_kind, reason="missing_health_report")

    phrase = _extract_phrase(text, investigation_kind)
    failed_rows = get_failed_health_rows(session_id=session_id, provider=provider)
    search_rows = failed_rows if investigation_kind in {"why_failed", "fix_plan", "status"} else rows
    matches = _match_rows(search_rows, phrase, text)
    if not matches:
        matches = _match_rows(search_rows, text, text)
    if not matches and investigation_kind in {"check_logs", "inspect_events"}:
        matches = _match_rows(rows, phrase, text)
    if not matches:
        matches = _match_rows(rows, text, text)

    if not matches:
        return FailedServiceResolution(ok=False, kind=investigation_kind, reason="service_not_found")

    unique = {row_key(row): row for row in matches}
    candidates = list(unique.values())
    if len(candidates) > 1:
        return FailedServiceResolution(
            ok=False,
            kind=investigation_kind,
            candidates=candidates,
            reason="ambiguous_service",
        )

    row = candidates[0]
    return FailedServiceResolution(
        ok=True,
        kind=investigation_kind,
        target=ResolvedFailedService(
            row=row,
            provider=provider,
            match_reason=f"matched `{phrase}` in last provider-wide health report",
            investigation_kind=investigation_kind,
        ),
    )


def is_failed_service_investigation_request(text: str, *, session_id: str = "default") -> bool:
    from aethos_core.failed_service_investigation.global_preemption import should_preempt_to_failed_service

    return should_preempt_to_failed_service(text, session_id=session_id)
