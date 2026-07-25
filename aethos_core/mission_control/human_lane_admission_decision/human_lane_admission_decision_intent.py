# SPDX-License-Identifier: Apache-2.0
"""FIX 176 — chat intent for human lane admission decision."""

from __future__ import annotations

import re

_HUMAN_LANE_ADMISSION_DECISION_RX = re.compile(
    r"\b("
    r"human\s+lane\s+admission\s+decision"
    r"|lane\s+admission\s+decision"
    r"|show\s+lane\s+admission\s+decision"
    r"|admission\s+decision\s+record"
    r"|lane\s+admit\s+decision"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*lane\s+admission\s+(?P<kind>decision|rationale|risk|reject|blocker|artifact|record)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_DECISION_RX = re.compile(
    r"^\s*lane\s+admission\s+decision\s+(?P<value>admit|hold|reject)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "decision": "lane_admission_decision_record",
    "rationale": "decision_rationale_note",
    "risk": "risk_tradeoff_acceptance_note",
    "reject": "rejected_candidate_note",
    "blocker": "acknowledged_blocker_note",
    "artifact": "lane_admission_decision_artifact",
    "record": "human_lane_admission_decision_record",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"enter\s+lane\s+now"
    r"|execute\s+lane\s+entry"
    r"|autonomous\s+admit"
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


def is_human_lane_admission_decision_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_HUMAN_LANE_ADMISSION_DECISION_RX.search(raw))


def parse_human_lane_admission_decision_record_intent(text: str) -> tuple[str, str] | None:
    raw = (text or "").strip()
    if not raw or _FORBIDDEN_RX.search(raw):
        return None

    decision_match = _DECISION_RX.match(raw)
    if decision_match:
        value = decision_match.group("value").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return "lane_admission_decision_record", f"{value}: {body}"

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
