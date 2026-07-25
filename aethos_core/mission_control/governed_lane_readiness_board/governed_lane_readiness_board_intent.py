# SPDX-License-Identifier: Apache-2.0
"""FIX 175 — chat intent for governed lane readiness board."""

from __future__ import annotations

import re

_GOVERNED_LANE_READINESS_BOARD_RX = re.compile(
    r"\b("
    r"governed\s+lane\s+readiness\s+board"
    r"|lane\s+readiness\s+board"
    r"|show\s+lane\s+readiness\s+board"
    r"|lane\s+admission\s+readiness\s+board"
    r"|readiness\s+board"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*lane\s+readiness\s+board\s+(?P<kind>artifact|candidate|blocker|gate|escalation|risk|forbidden|record)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "artifact": "lane_readiness_board_artifact",
    "candidate": "board_candidate_note",
    "blocker": "board_blocker_note",
    "gate": "board_gate_note",
    "escalation": "board_escalation_note",
    "risk": "board_risk_note",
    "forbidden": "forbidden_board_note",
    "record": "governed_lane_readiness_board_record",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"admit\s+to\s+lane"
    r"|lane\s+admission\s+decision"
    r"|lane\s+admission\s+now"
    r"|enter\s+lane\s+now"
    r"|bypass\s+gate"
    r"|execute\s+approval"
    r"|write\s+code"
    r"|open\s+pr"
    r"|merge\s+now"
    r"|deploy\s+now"
    r"|railway\s+mutation"
    r")\b",
    re.I,
)


def is_governed_lane_readiness_board_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_GOVERNED_LANE_READINESS_BOARD_RX.search(raw))


def parse_governed_lane_readiness_board_record_intent(text: str) -> tuple[str, str] | None:
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
