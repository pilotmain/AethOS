# SPDX-License-Identifier: Apache-2.0
"""FIX 148 — chat intent for governance deliberation workspace."""

from __future__ import annotations

import re

_DELIBERATION_RX = re.compile(
    r"\b("
    r"governance\s+deliberation"
    r"|deliberation\s+workspace"
    r"|show\s+deliberation"
    r"|reviewer\s+annotations?"
    r"|structured\s+concerns?"
    r"|dissent\s+tracking"
    r"|decision\s+justification"
    r"|governance\s+discussion\s+timeline"
    r"|why\s+was\s+this\s+approved"
    r"|why\s+was\s+this\s+rejected"
    r"|alternative[- ]path\s+comparison"
    r"|review\s+checklist"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*deliberation\s+(?P<kind>note|concern|dissent|rationale|annotation|justification)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "note": "operator_note",
    "concern": "structured_concern",
    "dissent": "dissent",
    "rationale": "rationale",
    "annotation": "reviewer_annotation",
    "justification": "decision_justification",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"auto\s+approve"
    r"|auto\s+reject"
    r"|autonomous\s+policy"
    r"|execute\s+deliberation"
    r")\b",
    re.I,
)


def is_governance_deliberation_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_DELIBERATION_RX.search(raw))


def parse_deliberation_record_intent(text: str) -> tuple[str, str] | None:
    raw = (text or "").strip()
    if not raw or _FORBIDDEN_RX.search(raw):
        return None
    match = _RECORD_RX.match(raw)
    if not match:
        return None
    kind_key = match.group("kind").lower()
    kind = _KIND_MAP.get(kind_key)
    if not kind:
        return None
    body = (match.group("body") or "").strip()
    if not body:
        return None
    return kind, body
