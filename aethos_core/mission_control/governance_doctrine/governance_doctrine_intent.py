# SPDX-License-Identifier: Apache-2.0
"""FIX 151 — chat intent for governance doctrine + policy charter."""

from __future__ import annotations

import re

_DOCTRINE_RX = re.compile(
    r"\b("
    r"governance\s+doctrine"
    r"|policy\s+charter"
    r"|governance\s+charter"
    r"|doctrine\s+version"
    r"|policy\s+rationale"
    r"|governance\s+principles?"
    r"|rule\s+lineage"
    r"|policy\s+amendment"
    r"|governance\s+precedent"
    r"|doctrine\s+conflict"
    r"|policy\s+freeze\s+snapshot"
    r"|constitutional\s+governance"
    r"|show\s+governance\s+doctrine"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*doctrine\s+(?P<kind>amendment|precedent|charter|rationale|reference)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "amendment": "policy_amendment_proposal",
    "precedent": "governance_precedent",
    "charter": "governance_charter",
    "rationale": "policy_rationale",
    "reference": "constitutional_reference",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"autonomous\s+doctrine"
    r"|self[- ]?modifying\s+governance"
    r"|auto\s+mutate\s+policy"
    r"|execute\s+amendment"
    r")\b",
    re.I,
)


def is_governance_doctrine_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_DOCTRINE_RX.search(raw))


def parse_doctrine_record_intent(text: str) -> tuple[str, str] | None:
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
