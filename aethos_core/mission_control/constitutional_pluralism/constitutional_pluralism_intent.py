# SPDX-License-Identifier: Apache-2.0
"""FIX 162 — chat intent for constitutional pluralism."""

from __future__ import annotations

import re

_CONSTITUTIONAL_PLURALISM_RX = re.compile(
    r"\b("
    r"constitutional\s+pluralism"
    r"|governance\s+perspective"
    r"|constitutional\s+worldview"
    r"|institutional\s+philosophy"
    r"|stakeholder\s+perspective"
    r"|competing\s+legitimacy\s+interpretation"
    r"|governance\s+culture\s+drift"
    r"|institutional\s+perspective\s+lineage"
    r"|constitutional\s+disagreement"
    r"|pluralistic\s+coherence"
    r"|show\s+constitutional\s+pluralism"
    r"|show\s+pluralism"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*pluralism\s+(?P<kind>perspective|worldview|philosophy|stakeholder|tracking|disagreement)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "perspective": "perspective_mapping_note",
    "worldview": "worldview_coexistence_note",
    "philosophy": "philosophy_comparison_note",
    "stakeholder": "stakeholder_perspective_note",
    "tracking": "pluralism_tracking_record",
    "disagreement": "disagreement_mapping_note",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"authoritative\s+worldview\s+selection"
    r"|autonomous\s+constitutional\s+arbitration"
    r"|enforced\s+ideological\s+alignment"
    r"|sovereignty\s+delegation"
    r"|select\s+worldview\s+autonomously"
    r"|arbitrate\s+constitutionally\s+autonomously"
    r")\b",
    re.I,
)


def is_constitutional_pluralism_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_CONSTITUTIONAL_PLURALISM_RX.search(raw))


def parse_pluralism_record_intent(text: str) -> tuple[str, str] | None:
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
