# SPDX-License-Identifier: Apache-2.0
"""FIX 184 — chat intent for issue intent alignment."""

from __future__ import annotations

import re

_INTENT_ALIGNMENT_RX = re.compile(
    r"\b("
    r"show\s+intent\s+alignment"
    r"|intent\s+alignment"
    r"|patch\s+target\s+validation"
    r"|issue\s+intent\s+alignment"
    r"|alignment\s+assessment"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*alignment\s+(?P<kind>artifact|review|escalation|note|record)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "artifact": "alignment_artifact",
    "review": "alignment_review_acknowledged",
    "escalation": "alignment_escalation_reviewed",
    "note": "misalignment_note",
    "record": "alignment_record",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"propose\s+patch"
    r"|apply\s+patch"
    r"|run\s+pilot"
    r"|bypass\s+gate"
    r"|direct\s+provider"
    r"|autonomous\s+patch"
    r")\b",
    re.I,
)


def is_issue_intent_alignment_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_INTENT_ALIGNMENT_RX.search(raw))


def parse_issue_intent_alignment_record_intent(text: str) -> tuple[str, str] | None:
    raw = (text or "").strip()
    if not raw:
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
