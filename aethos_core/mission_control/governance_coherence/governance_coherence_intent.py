# SPDX-License-Identifier: Apache-2.0
"""FIX 153 — chat intent for governance coherence + constitutional integrity."""

from __future__ import annotations

import re

_COHERENCE_RX = re.compile(
    r"\b("
    r"governance\s+coherence"
    r"|constitutional\s+integrity"
    r"|doctrine[\-\s]topology\s+consistency"
    r"|precedent\s+drift"
    r"|governance\s+contradiction"
    r"|institutional\s+integrity"
    r"|policy\s+fragmentation"
    r"|principle\s+alignment"
    r"|cross[\-\s]session\s+doctrine"
    r"|conflicting\s+precedent"
    r"|trust[\-\s]boundary\s+consistency"
    r"|governance\s+stability"
    r"|show\s+governance\s+coherence"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*coherence\s+(?P<kind>observation|contradiction|drift|integrity|stability)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "observation": "coherence_observation",
    "contradiction": "contradiction_report",
    "drift": "drift_signal",
    "integrity": "integrity_note",
    "stability": "stability_note",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"automatic\s+doctrine\s+enforcement"
    r"|autonomous\s+governance\s+correction"
    r"|self[\-\s]?healing\s+governance"
    r"|constitutional\s+override"
    r"|auto\s+correct\s+governance"
    r"|enforce\s+coherence"
    r")\b",
    re.I,
)


def is_governance_coherence_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_COHERENCE_RX.search(raw))


def parse_coherence_record_intent(text: str) -> tuple[str, str] | None:
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
