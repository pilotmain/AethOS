# SPDX-License-Identifier: Apache-2.0
"""FIX 200 — chat intent for governed merge lifecycle."""

from __future__ import annotations

import re

_VIEW_RX = re.compile(
    r"\b("
    r"show\s+(?:governed\s+)?merge\s+(?:lifecycle|readiness|review)"
    r"|merge\s+review\s+packet"
    r"|merge\s+readiness\s+report"
    r"|governed\s+merge\s+lifecycle"
    r")\b",
    re.I,
)

_HANDOFF_RX = re.compile(
    r"\b(prepare\s+merge\s+handoff|generate\s+merge\s+execution\s+request)\b",
    re.I,
)

_DECISION_RX = re.compile(
    r"^\s*merge\s+decision\s+(?P<decision>approve|hold|reject)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_NOTE_RX = re.compile(
    r"^\s*merge\s+review\s+(?P<kind>observation|note)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_DECISION_KIND_MAP = {
    "approve": "merge_decision_approve",
    "hold": "merge_decision_hold",
    "reject": "merge_decision_reject",
}

_NOTE_KIND_MAP = {
    "observation": "merge_review_observation",
    "note": "merge_rationale_note",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"autonomous\s+merge"
    r"|auto\s+merge"
    r"|bypass\s+merge\s+approval"
    r"|hidden\s+merge"
    r")\b",
    re.I,
)


def is_governed_merge_lifecycle_intent(text: str) -> bool:
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


def is_governed_merge_handoff_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw or _FORBIDDEN_RX.search(raw):
        return False
    return bool(_HANDOFF_RX.search(raw))


def parse_governed_merge_lifecycle_record_intent(text: str) -> tuple[str, str] | None:
    raw = (text or "").strip()
    decision_match = _DECISION_RX.match(raw)
    if decision_match:
        kind = _DECISION_KIND_MAP.get(decision_match.group("decision").lower())
        body = (decision_match.group("body") or "").strip()
        if kind and body:
            return kind, body
    note_match = _NOTE_RX.match(raw)
    if note_match:
        kind = _NOTE_KIND_MAP.get(note_match.group("kind").lower())
        body = (note_match.group("body") or "").strip()
        if kind and body:
            return kind, body
    return None
