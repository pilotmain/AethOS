# SPDX-License-Identifier: Apache-2.0
"""FIX 166 — chat intent for human decision board."""

from __future__ import annotations

import re

_HUMAN_DECISION_BOARD_RX = re.compile(
    r"\b("
    r"human\s+decision\s+board"
    r"|action\s+selection"
    r"|candidate\s+action\s+board"
    r"|human\s+selection"
    r"|decision\s+record"
    r"|decision\s+traceability"
    r"|decision\s+review\s+package"
    r"|rejected\s+paths?"
    r"|decision\s+rationale"
    r"|execution\s+handoff"
    r"|show\s+human\s+decision"
    r"|show\s+decision\s+board"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*decision\s+(?P<kind>select|reject|rationale|tradeoff|risk|artifact|approval|handoff)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "select": "selection_record",
    "reject": "rejection_note",
    "rationale": "rationale_note",
    "tradeoff": "tradeoff_acceptance_note",
    "risk": "risk_acceptance_note",
    "artifact": "decision_artifact",
    "approval": "approval_artifact",
    "handoff": "execution_handoff_artifact",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"autonomous\s+selection"
    r"|autonomous\s+execution"
    r"|autonomous\s+approval"
    r"|autonomous\s+pr"
    r"|autonomous\s+merge"
    r"|mutate\s+railway"
    r"|auto[\-\s]?select\s+path"
    r"|system\s+selects?\s+path"
    r")\b",
    re.I,
)


def is_human_decision_board_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_HUMAN_DECISION_BOARD_RX.search(raw))


def parse_decision_record_intent(text: str) -> tuple[str, str] | None:
    raw = (text or "").strip()
    if not raw or _FORBIDDEN_RX.search(raw):
        return None
    match = _RECORD_RX.match(raw)
    if not match:
        return None
    kind = _KIND_MAP.get(match.group("kind").lower())
    if not kind:
        return None
    body = (match.group("body") or "").strip()
    if not body:
        return None
    return kind, body
