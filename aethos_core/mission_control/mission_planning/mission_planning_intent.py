# SPDX-License-Identifier: Apache-2.0
"""FIX 164 — chat intent for mission planning."""

from __future__ import annotations

import re

_MISSION_PLANNING_RX = re.compile(
    r"\b("
    r"mission\s+planning"
    r"|institutional\s+action"
    r"|action\s+options?"
    r"|compare\s+action\s+options?"
    r"|lane\s+selection"
    r"|required\s+approvals?"
    r"|mission\s+action\s+plan"
    r"|do\s+not\s+do\s+path"
    r"|operator\s+review\s+sequence"
    r"|institutional\s+course\s+of\s+action"
    r"|show\s+mission\s+planning"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*planning\s+(?P<kind>option|comparison|lane|approval|tradeoff|risk|avoid|sequence|artifact)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "option": "action_option_note",
    "comparison": "option_comparison_note",
    "lane": "lane_mapping_note",
    "approval": "required_approval_note",
    "tradeoff": "constitutional_tradeoff_note",
    "risk": "risk_blocker_note",
    "avoid": "do_not_do_path_note",
    "sequence": "review_sequence_note",
    "artifact": "mission_action_plan_artifact",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"execute\s+action"
    r"|approve\s+action"
    r"|auto[\-\s]?select\s+path"
    r"|open\s+pr"
    r"|mutate\s+railway"
    r"|merge\s+deploy"
    r"|deploy\s+restart"
    r"|autonomous\s+lane\s+selection"
    r"|autonomous\s+execution"
    r")\b",
    re.I,
)


def is_mission_planning_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_MISSION_PLANNING_RX.search(raw))


def parse_planning_record_intent(text: str) -> tuple[str, str] | None:
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
