# SPDX-License-Identifier: Apache-2.0
"""FIX 230 — chat intent for governed rollback lifecycle."""

from __future__ import annotations

import re
from typing import Any

_VIEW_RX = re.compile(
    r"\b("
    r"show\s+(?:governed\s+)?rollback\s+(?:lifecycle|assessment|review)"
    r"|rollback\s+assessment\s+report"
    r"|rollback\s+review\s+packet"
    r"|governed\s+rollback\s+lifecycle"
    r")\b",
    re.I,
)

_HANDOFF_RX = re.compile(
    r"\b(prepare\s+rollback\s+handoff|generate\s+rollback\s+execution\s+request)\b",
    re.I,
)

_DECISION_RX = re.compile(
    r"^\s*rollback\s+decision\s+(?P<decision>approve|hold|reject)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_NOTE_RX = re.compile(
    r"^\s*rollback\s+(?P<kind>candidate|risk|assessment)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_DECISION_KIND_MAP = {
    "approve": "rollback_decision_approve",
    "hold": "rollback_decision_hold",
    "reject": "rollback_decision_reject",
}

_NOTE_KIND_MAP = {
    "candidate": "rollback_candidate_note",
    "risk": "rollback_risk_note",
    "assessment": "rollback_assessment_note",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"autonomous\s+rollback"
    r"|execute\s+rollback\s+now"
    r"|auto\s+rollback"
    r"|mutate\s+database"
    r")\b",
    re.I,
)

_TARGET_RX = re.compile(r"\btarget\s*=\s*([^\s]+)", re.I)
_RELEASE_RX = re.compile(r"\brelease\s*=\s*([^\s]+)", re.I)


def _parse_candidate_metadata(text: str) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    target = _TARGET_RX.search(text or "")
    if target:
        meta["rollback_target"] = target.group(1).strip()
    release = _RELEASE_RX.search(text or "")
    if release:
        meta["target_release"] = release.group(1).strip()
    return meta


def is_governed_rollback_lifecycle_intent(text: str) -> bool:
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
    )


def is_governed_rollback_handoff_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw or _FORBIDDEN_RX.search(raw):
        return False
    return bool(_HANDOFF_RX.search(raw))


def parse_governed_rollback_lifecycle_record_intent(
    text: str,
) -> tuple[str, str, dict[str, Any]] | None:
    raw = (text or "").strip()

    decision_match = _DECISION_RX.match(raw)
    if decision_match:
        kind = _DECISION_KIND_MAP.get(decision_match.group("decision").lower())
        body = (decision_match.group("body") or "").strip()
        if kind and body:
            return kind, body, {}

    note_match = _NOTE_RX.match(raw)
    if note_match:
        kind = _NOTE_KIND_MAP.get(note_match.group("kind").lower())
        body = (note_match.group("body") or "").strip()
        if kind and body:
            meta = _parse_candidate_metadata(body) if kind == "rollback_candidate_note" else {}
            return kind, body, meta

    return None
