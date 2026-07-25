# SPDX-License-Identifier: Apache-2.0
"""FIX 165 — chat intent for mission planning multi-agent deliberation."""

from __future__ import annotations

import re

_MISSION_PLANNING_DELIBERATION_RX = re.compile(
    r"\b("
    r"mission\s+planning\s+deliberation"
    r"|planning\s+deliberation"
    r"|multi[\-\s]agent\s+deliberation"
    r"|agent\s+deliberation"
    r"|consolidated\s+recommendation"
    r"|bounded\s+agent\s+analysis"
    r"|planner\s+agent\s+analysis"
    r"|deliberation\s+integrity"
    r"|show\s+deliberation"
    r"|show\s+planning\s+deliberation"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*deliberation\s+(?P<kind>planner|risk|constitutional|delivery|verification|synthesis|record)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "planner": "planner_analysis_note",
    "risk": "risk_analysis_note",
    "constitutional": "constitutional_analysis_note",
    "delivery": "delivery_analysis_note",
    "verification": "verification_analysis_note",
    "synthesis": "synthesis_summary_note",
    "record": "deliberation_record",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"autonomous\s+execution"
    r"|autonomous\s+approval"
    r"|autonomous\s+lane\s+selection"
    r"|autonomous\s+pr"
    r"|mutate\s+railway"
    r"|autonomous\s+merge"
    r"|execute\s+deliberation\s+autonomously"
    r")\b",
    re.I,
)


def is_mission_planning_deliberation_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_MISSION_PLANNING_DELIBERATION_RX.search(raw))


def parse_deliberation_record_intent(text: str) -> tuple[str, str] | None:
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
