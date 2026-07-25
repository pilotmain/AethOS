# SPDX-License-Identifier: Apache-2.0
"""FIX 154 — chat intent for governance resilience + stress simulation."""

from __future__ import annotations

import re

_RESILIENCE_RX = re.compile(
    r"\b("
    r"governance\s+resilience"
    r"|institutional\s+resilience"
    r"|governance\s+stress"
    r"|stress\s+simulation"
    r"|approval[\-\s]chain\s+overload"
    r"|incident\s+surge\s+resilience"
    r"|quorum\s+failure"
    r"|governance\s+fragmentation\s+stress"
    r"|operator\s+loss"
    r"|handoff\s+resilience"
    r"|doctrine\s+conflict\s+escalation"
    r"|trust[\-\s]boundary\s+breach"
    r"|governance\s+recovery\s+posture"
    r"|resilience\s+scoring"
    r"|show\s+governance\s+resilience"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*resilience\s+(?P<kind>scenario|observation|recovery|handoff|breach)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "scenario": "stress_scenario",
    "observation": "resilience_observation",
    "recovery": "recovery_posture_note",
    "handoff": "handoff_stress_note",
    "breach": "breach_simulation_note",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"automatic\s+governance\s+adaptation"
    r"|autonomous\s+resilience\s+correction"
    r"|self[\-\s]?healing\s+governance"
    r"|override\s+authority"
    r"|apply\s+stress\s+simulation"
    r"|live\s+adaptation"
    r"|auto\s+correct\s+resilience"
    r")\b",
    re.I,
)


def is_governance_resilience_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_RESILIENCE_RX.search(raw))


def parse_resilience_record_intent(text: str) -> tuple[str, str] | None:
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
