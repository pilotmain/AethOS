# SPDX-License-Identifier: Apache-2.0
"""FIX 194 — chat intent for Atlas Trader trust report freeze."""

from __future__ import annotations

import re

_ATLAS_TRUST_FREEZE_RX = re.compile(
    r"\b("
    r"atlas\s+(?:trader\s+)?trust\s+(?:report|baseline|freeze)"
    r"|show\s+atlas\s+(?:trader\s+)?trust\s+(?:report\s+freeze|freeze)"
    r"|atlas\s+trust\s+report\s+freeze"
    r"|frozen\s+atlas\s+evidence"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*atlas\s+trust\s+(?P<kind>freeze|review|boundary|intervention|decision)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_DECISION_RX = re.compile(
    r"^\s*atlas\s+trust\s+decision\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "freeze": "atlas_trust_report_freeze_artifact",
    "review": "operator_review_note",
    "boundary": "trust_boundary_note",
    "intervention": "intervention_note",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"run\s+atlas\s+pilot"
    r"|rerun\s+pilot"
    r"|re-?execute\s+pilot"
    r"|bypass\s+gate"
    r"|auto\s+grant\s+trust"
    r"|inherit\s+trust"
    r")\b",
    re.I,
)


def is_atlas_trader_trust_report_freeze_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_ATLAS_TRUST_FREEZE_RX.search(raw))


def parse_atlas_trader_trust_report_freeze_record_intent(text: str) -> tuple[str, str] | None:
    raw = (text or "").strip()
    if not raw:
        return None

    decision_match = _DECISION_RX.match(raw)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return f"human_trust_decision_{decision}", body

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
