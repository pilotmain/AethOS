# SPDX-License-Identifier: Apache-2.0
"""FIX 155 — chat intent for governance evolution + institutional continuity."""

from __future__ import annotations

import re

_EVOLUTION_RX = re.compile(
    r"\b("
    r"governance\s+evolution"
    r"|institutional\s+continuity"
    r"|doctrine\s+era"
    r"|governance\s+generation"
    r"|institutional\s+transition"
    r"|freeze[\-\s]era\s+continuity"
    r"|governance\s+maturity"
    r"|long[\-\s]horizon\s+drift"
    r"|constitutional\s+epoch"
    r"|governance\s+migration"
    r"|continuity\s+scoring"
    r"|historical\s+governance\s+narrative"
    r"|show\s+governance\s+evolution"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*evolution\s+(?P<kind>era|generation|transition|continuity|narrative)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "era": "doctrine_era",
    "generation": "generation_marker",
    "transition": "transition_note",
    "continuity": "continuity_observation",
    "narrative": "narrative_record",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"autonomous\s+governance\s+evolution"
    r"|self[\-\s]?directed\s+institutional\s+transformation"
    r"|automatic\s+doctrine\s+migration"
    r"|policy\s+mutation\s+authority"
    r"|auto\s+evolve\s+governance"
    r"|execute\s+doctrine\s+migration"
    r")\b",
    re.I,
)


def is_governance_evolution_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_EVOLUTION_RX.search(raw))


def parse_evolution_record_intent(text: str) -> tuple[str, str] | None:
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
