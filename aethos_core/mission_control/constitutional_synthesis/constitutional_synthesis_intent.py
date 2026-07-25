# SPDX-License-Identifier: Apache-2.0
"""FIX 163 — chat intent for constitutional synthesis."""

from __future__ import annotations

import re

_CONSTITUTIONAL_SYNTHESIS_RX = re.compile(
    r"\b("
    r"constitutional\s+synthesis"
    r"|institutional\s+wisdom"
    r"|constitutional\s+tension"
    r"|constitutional\s+tradeoff"
    r"|cross[\-\s]dimensional\s+synthesis"
    r"|inter[\-\s]dimensional"
    r"|recurring\s+constitutional\s+tension"
    r"|constitutional\s+layer\s+interaction"
    r"|synthesis\s+coherence"
    r"|wisdom\s+continuity"
    r"|show\s+constitutional\s+synthesis"
    r"|show\s+synthesis"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*synthesis\s+(?P<kind>tension|tradeoff|cross|wisdom|pattern)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "tension": "tension_analysis_note",
    "tradeoff": "tradeoff_map_note",
    "cross": "cross_dimensional_synthesis_note",
    "wisdom": "wisdom_signal",
    "pattern": "recurring_pattern_note",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"autonomous\s+constitutional\s+decisions?"
    r"|doctrine\s+enforcement"
    r"|legitimacy\s+arbitration"
    r"|worldview\s+selection"
    r"|sovereignty\s+delegation"
    r"|enforce\s+doctrine\s+autonomously"
    r"|decide\s+constitutional\s+tradeoff\s+autonomously"
    r")\b",
    re.I,
)


def is_constitutional_synthesis_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_CONSTITUTIONAL_SYNTHESIS_RX.search(raw))


def parse_synthesis_record_intent(text: str) -> tuple[str, str] | None:
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
