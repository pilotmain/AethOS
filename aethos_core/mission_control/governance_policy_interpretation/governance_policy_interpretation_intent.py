# SPDX-License-Identifier: Apache-2.0
"""FIX 152 — chat intent for governance policy interpretation."""

from __future__ import annotations

import re

_INTERPRETATION_RX = re.compile(
    r"\b("
    r"governance\s+policy\s+interpretation"
    r"|governance\s+interpretation"
    r"|doctrine\s+interpretation"
    r"|precedent\s+application"
    r"|interpretation\s+guidance"
    r"|governance\s+rationale\s+mapping"
    r"|doctrine[\-\s]to[\-\s]review\s+linkage"
    r"|precedent\s+confidence"
    r"|competing\s+interpretation"
    r"|governance\s+ambiguity"
    r"|interpretation\s+continuity"
    r"|constitutional\s+consistency"
    r"|show\s+governance\s+interpretation"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*interpretation\s+(?P<kind>doctrine|precedent|guidance|rationale|linkage|competing|ambiguity|history)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "doctrine": "doctrine_interpretation",
    "precedent": "precedent_application",
    "guidance": "interpretation_guidance",
    "rationale": "rationale_mapping",
    "linkage": "doctrine_review_linkage",
    "competing": "competing_interpretation",
    "ambiguity": "ambiguity_surfacing",
    "history": "historical_interpretation",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"automatic\s+doctrine\s+enforcement"
    r"|autonomous\s+governance\s+ruling"
    r"|auto\s+mutate\s+policy"
    r"|enforce\s+doctrine"
    r"|execute\s+ruling"
    r"|automatic\s+governance\s+ruling"
    r")\b",
    re.I,
)


def is_governance_policy_interpretation_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_INTERPRETATION_RX.search(raw))


def parse_interpretation_record_intent(text: str) -> tuple[str, str] | None:
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
