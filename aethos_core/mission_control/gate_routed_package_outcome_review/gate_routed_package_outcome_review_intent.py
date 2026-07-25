# SPDX-License-Identifier: Apache-2.0
"""FIX 173 — chat intent for gate-routed package outcome review."""

from __future__ import annotations

import re

_GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_RX = re.compile(
    r"\b("
    r"gate.?routed\s+package\s+outcome\s+review"
    r"|package\s+outcome\s+review"
    r"|gate\s+review\s+packet"
    r"|review\s+package\s+outcomes"
    r"|outcome\s+quality"
    r"|frozen\s+gate\s+mapping"
    r"|show\s+gate\s+review"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*gate\s+review\s+(?P<kind>artifact|quality|incomplete|escalation|mapping|forbidden|record)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "artifact": "gate_review_artifact",
    "quality": "outcome_quality_note",
    "incomplete": "incomplete_package_note",
    "escalation": "escalation_review_note",
    "mapping": "gate_mapping_note",
    "forbidden": "forbidden_review_note",
    "record": "gate_routed_package_outcome_review_record",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"execute\s+now"
    r"|bypass\s+gate"
    r"|bypass\s+approval"
    r"|write\s+code"
    r"|open\s+pr"
    r"|merge\s+now"
    r"|deploy\s+now"
    r"|railway\s+mutation"
    r")\b",
    re.I,
)


def is_gate_routed_package_outcome_review_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_RX.search(raw))


def parse_gate_routed_package_outcome_review_record_intent(text: str) -> tuple[str, str] | None:
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
