# SPDX-License-Identifier: Apache-2.0
"""FIX 156 — chat intent for institutional identity + constitutional intent."""

from __future__ import annotations

import re

_IDENTITY_RX = re.compile(
    r"\b("
    r"institutional\s+identity"
    r"|constitutional\s+intent"
    r"|mission\s+identity"
    r"|operational\s+philosophy"
    r"|governance\s+purpose"
    r"|institutional\s+value\s+drift"
    r"|constitutional\s+mission\s+alignment"
    r"|organizational\s+identity"
    r"|doctrine[\-\s]purpose\s+consistency"
    r"|intent\s+reconstruction"
    r"|institutional\s+narrative"
    r"|show\s+institutional\s+identity"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*identity\s+(?P<kind>mission|intent|philosophy|purpose|continuity|narrative)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "mission": "mission_identity",
    "intent": "constitutional_intent",
    "philosophy": "philosophy_record",
    "purpose": "purpose_preservation",
    "continuity": "identity_continuity",
    "narrative": "narrative_continuity",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"autonomous\s+institutional\s+redirection"
    r"|self[\-\s]?authored\s+mission"
    r"|automatic\s+constitutional\s+rewriting"
    r"|governance\s+sovereignty\s+delegation"
    r"|auto\s+redirect\s+institution"
    r"|rewrite\s+constitutional\s+intent"
    r")\b",
    re.I,
)


def is_institutional_identity_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_IDENTITY_RX.search(raw))


def parse_identity_record_intent(text: str) -> tuple[str, str] | None:
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
