# SPDX-License-Identifier: Apache-2.0
"""FIX 174 — chat intent for governed lane entry recommendation."""

from __future__ import annotations

import re

_GOVERNED_LANE_ENTRY_RECOMMENDATION_RX = re.compile(
    r"\b("
    r"governed\s+lane\s+entry\s+recommendation"
    r"|lane\s+entry\s+recommendation"
    r"|recommend\s+lane\s+entry"
    r"|lane\s+recommendation"
    r"|show\s+lane\s+recommendation"
    r"|eligible\s+lane\s+candidates"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*lane\s+recommendation\s+(?P<kind>artifact|eligibility|blocked|escalation|gate|forbidden|record)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "artifact": "lane_recommendation_artifact",
    "eligibility": "eligibility_rationale_note",
    "blocked": "blocked_lane_note",
    "escalation": "escalation_recommendation_note",
    "gate": "next_gate_note",
    "forbidden": "forbidden_recommendation_note",
    "record": "governed_lane_entry_recommendation_record",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"enter\s+lane\s+now"
    r"|admit\s+to\s+lane"
    r"|lane\s+admission\s+now"
    r"|bypass\s+gate"
    r"|execute\s+now"
    r"|write\s+code"
    r"|open\s+pr"
    r"|merge\s+now"
    r"|deploy\s+now"
    r"|railway\s+mutation"
    r")\b",
    re.I,
)


def is_governed_lane_entry_recommendation_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_GOVERNED_LANE_ENTRY_RECOMMENDATION_RX.search(raw))


def parse_governed_lane_entry_recommendation_record_intent(text: str) -> tuple[str, str] | None:
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
