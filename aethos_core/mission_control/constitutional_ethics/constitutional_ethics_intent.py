# SPDX-License-Identifier: Apache-2.0
"""FIX 159 — chat intent for constitutional ethics."""

from __future__ import annotations

import re

_CONSTITUTIONAL_ETHICS_RX = re.compile(
    r"\b("
    r"constitutional\s+ethics"
    r"|institutional\s+moral\s+reasoning"
    r"|value[\-\s]conflict\s+reasoning"
    r"|moral\s+tradeoff"
    r"|ethical\s+tension"
    r"|constitutional\s+ethics\s+continuity"
    r"|long[\-\s]horizon\s+value\s+preservation"
    r"|ethical\s+ambiguity"
    r"|moral\s+precedent"
    r"|constitutional\s+value\s+drift"
    r"|ethical\s+coherence"
    r"|show\s+constitutional\s+ethics"
    r"|show\s+ethics"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*ethical\s+(?P<kind>value|conflict|tradeoff|tension|preservation|precedent)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "value": "ethics_record",
    "conflict": "value_conflict_note",
    "tradeoff": "moral_tradeoff",
    "tension": "ethical_tension_observation",
    "preservation": "value_preservation_note",
    "precedent": "moral_precedent",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"autonomous\s+moral\s+authority"
    r"|self[\-\s]?authored\s+ethics"
    r"|constitutional\s+override"
    r"|value[\-\s]?enforcement\s+authority"
    r"|enforce\s+values\s+autonomously"
    r"|author\s+ethics\s+autonomously"
    r")\b",
    re.I,
)


def is_constitutional_ethics_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_CONSTITUTIONAL_ETHICS_RX.search(raw))


def parse_ethics_record_intent(text: str) -> tuple[str, str] | None:
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
