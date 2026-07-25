# SPDX-License-Identifier: Apache-2.0
"""FIX 160 — chat intent for constitutional audit."""

from __future__ import annotations

import re

_CONSTITUTIONAL_AUDIT_RX = re.compile(
    r"\b("
    r"constitutional\s+audit"
    r"|public\s+accountability"
    r"|traceable\s+reasoning"
    r"|recommendation\s+explanation"
    r"|why\s+did\s+aethos\s+recommend"
    r"|accountability\s+record"
    r"|governance\s+evidence\s+bundle"
    r"|public[\-\s]safe\s+accountability"
    r"|disclosure\s+boundary"
    r"|constitutional\s+transparency"
    r"|audit\s+trail\s+integrity"
    r"|show\s+constitutional\s+audit"
    r"|show\s+audit"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*audit\s+(?P<kind>report|reasoning|accountability|explanation|disclosure)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "report": "audit_report",
    "reasoning": "reasoning_summary",
    "accountability": "accountability_record",
    "explanation": "recommendation_explanation",
    "disclosure": "disclosure_boundary_note",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"autonomous\s+disclosure"
    r"|public\s+communication\s+authority"
    r"|governance\s+enforcement"
    r"|auto[\-\s]?disclose"
    r"|enforce\s+governance\s+autonomously"
    r"|publish\s+publicly\s+autonomously"
    r")\b",
    re.I,
)


def is_constitutional_audit_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_CONSTITUTIONAL_AUDIT_RX.search(raw))


def parse_audit_record_intent(text: str) -> tuple[str, str] | None:
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
