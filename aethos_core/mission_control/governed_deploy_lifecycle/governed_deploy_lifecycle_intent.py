# SPDX-License-Identifier: Apache-2.0
"""FIX 210 — chat intent for governed deploy lifecycle."""

from __future__ import annotations

import re
from typing import Any

_VIEW_RX = re.compile(
    r"\b("
    r"show\s+(?:governed\s+)?deploy\s+(?:lifecycle|readiness|review)"
    r"|deploy\s+review\s+packet"
    r"|deploy\s+readiness\s+report"
    r"|governed\s+deploy\s+lifecycle"
    r")\b",
    re.I,
)

_HANDOFF_RX = re.compile(
    r"\b(prepare\s+deploy\s+handoff|generate\s+deployment\s+execution\s+request)\b",
    re.I,
)

_DECISION_RX = re.compile(
    r"^\s*deploy\s+decision\s+(?P<decision>approve|hold|reject)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_NOTE_RX = re.compile(
    r"^\s*deploy\s+review\s+(?P<kind>observation|note)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_MERGE_ACK_RX = re.compile(
    r"^\s*merge\s+completed\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_DECISION_KIND_MAP = {
    "approve": "deploy_decision_approve",
    "hold": "deploy_decision_hold",
    "reject": "deploy_decision_reject",
}

_NOTE_KIND_MAP = {
    "observation": "deploy_review_observation",
    "note": "deploy_rationale_note",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"autonomous\s+deploy"
    r"|auto\s+deploy"
    r"|railway\s+deploy"
    r"|vercel\s+deploy"
    r"|hidden\s+workflow"
    r")\b",
    re.I,
)

_ENV_RX = re.compile(r"\benvironment\s*=\s*(development|staging)\b", re.I)


def _parse_environment(text: str) -> str | None:
    match = _ENV_RX.search(text or "")
    if match:
        return match.group(1).lower()
    lowered = (text or "").lower()
    if "staging" in lowered:
        return "staging"
    if "development" in lowered or "dev environment" in lowered:
        return "development"
    return None


def is_governed_deploy_lifecycle_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(
        _VIEW_RX.search(raw)
        or _HANDOFF_RX.search(raw)
        or _DECISION_RX.match(raw)
        or _NOTE_RX.match(raw)
        or _MERGE_ACK_RX.match(raw)
    )


def is_governed_deploy_handoff_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw or _FORBIDDEN_RX.search(raw):
        return False
    return bool(_HANDOFF_RX.search(raw))


def parse_governed_deploy_lifecycle_record_intent(
    text: str,
) -> tuple[str, str, dict[str, Any]] | None:
    raw = (text or "").strip()
    merge_match = _MERGE_ACK_RX.match(raw)
    if merge_match:
        body = (merge_match.group("body") or "").strip()
        if body:
            return "merge_completed_acknowledgment", body, {}

    decision_match = _DECISION_RX.match(raw)
    if decision_match:
        kind = _DECISION_KIND_MAP.get(decision_match.group("decision").lower())
        body = (decision_match.group("body") or "").strip()
        if kind and body:
            metadata: dict[str, Any] = {}
            env = _parse_environment(body)
            if env and kind == "deploy_decision_approve":
                metadata["environment"] = env
            return kind, body, metadata

    note_match = _NOTE_RX.match(raw)
    if note_match:
        kind = _NOTE_KIND_MAP.get(note_match.group("kind").lower())
        body = (note_match.group("body") or "").strip()
        if kind and body:
            return kind, body, {}

    return None
