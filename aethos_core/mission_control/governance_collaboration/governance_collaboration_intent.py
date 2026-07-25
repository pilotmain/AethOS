# SPDX-License-Identifier: Apache-2.0
"""FIX 149 — chat intent for multi-operator governance collaboration."""

from __future__ import annotations

import re

_COLLABORATION_RX = re.compile(
    r"\b("
    r"multi[- ]operator\s+governance"
    r"|governance\s+collaboration"
    r"|show\s+governance\s+collaboration"
    r"|named\s+reviewers?"
    r"|role[- ]aware\s+deliberation"
    r"|quorum[- ]aware\s+discussion"
    r"|review\s+ownership"
    r"|delegated\s+review\s+request"
    r"|reviewer\s+assignment"
    r"|reviewer\s+acknowledgment"
    r"|governance\s+handoff"
    r"|unresolved\s+concern\s+escalation"
    r"|decision\s+participation\s+graph"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*collaboration\s+(?P<kind>assign|acknowledge|handoff|escalate|request)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "assign": "reviewer_assignment",
    "acknowledge": "reviewer_acknowledgment",
    "handoff": "governance_handoff",
    "escalate": "unresolved_concern_escalation",
    "request": "delegated_review_request",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"auto\s+quorum\s+approv"
    r"|autonomous\s+organizational"
    r"|delegated\s+execution"
    r"|auto\s+merge"
    r"|auto\s+deploy"
    r")\b",
    re.I,
)


def is_governance_collaboration_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_COLLABORATION_RX.search(raw))


def parse_collaboration_record_intent(text: str) -> tuple[str, str] | None:
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
