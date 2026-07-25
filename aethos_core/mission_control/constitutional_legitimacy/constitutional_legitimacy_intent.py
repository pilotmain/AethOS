# SPDX-License-Identifier: Apache-2.0
"""FIX 161 — chat intent for constitutional legitimacy."""

from __future__ import annotations

import re

_CONSTITUTIONAL_LEGITIMACY_RX = re.compile(
    r"\b("
    r"constitutional\s+legitimacy"
    r"|institutional\s+trust"
    r"|governance\s+legitimacy"
    r"|stakeholder\s+confidence"
    r"|constitutional\s+credibility"
    r"|trust\s+fragmentation"
    r"|institutional\s+confidence\s+scoring"
    r"|legitimacy\s+continuity"
    r"|constitutional\s+participation\s+health"
    r"|governance\s+transparency\s+trust"
    r"|credibility\s+reconstruction"
    r"|show\s+constitutional\s+legitimacy"
    r"|show\s+legitimacy"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*legitimacy\s+(?P<kind>trust|indicator|confidence|credibility|tracking)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "trust": "trust_continuity_note",
    "indicator": "legitimacy_indicator",
    "confidence": "stakeholder_confidence_note",
    "credibility": "credibility_drift_signal",
    "tracking": "legitimacy_tracking_record",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"autonomous\s+legitimacy\s+enforcement"
    r"|public\s+trust\s+manipulation"
    r"|constitutional\s+authority\s+expansion"
    r"|sovereignty\s+delegation"
    r"|manipulate\s+public\s+trust"
    r"|enforce\s+legitimacy\s+autonomously"
    r")\b",
    re.I,
)


def is_constitutional_legitimacy_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_CONSTITUTIONAL_LEGITIMACY_RX.search(raw))


def parse_legitimacy_record_intent(text: str) -> tuple[str, str] | None:
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
