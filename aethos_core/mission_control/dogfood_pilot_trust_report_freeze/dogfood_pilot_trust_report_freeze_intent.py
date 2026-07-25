# SPDX-License-Identifier: Apache-2.0
"""FIX 186 — chat intent for dogfood pilot trust report freeze."""

from __future__ import annotations

import re

_TRUST_REPORT_FREEZE_RX = re.compile(
    r"\b("
    r"dogfood\s+(?:pilot\s+)?trust\s+(?:report|baseline)"
    r"|show\s+(?:dogfood\s+)?trust\s+report\s+freeze"
    r"|trust\s+report\s+freeze"
    r"|dogfood\s+trust\s+baseline"
    r"|frozen\s+dogfood\s+evidence"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*trust\s+report\s+(?P<kind>freeze|review|expansion|boundary)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "freeze": "trust_report_freeze_artifact",
    "review": "operator_review_note",
    "expansion": "expansion_approval_note",
    "boundary": "trust_boundary_note",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"run\s+pilot"
    r"|rerun\s+pilot"
    r"|re-?execute\s+pilot"
    r"|bypass\s+gate"
    r"|direct\s+provider"
    r"|hidden\s+execute"
    r"|auto\s+expand"
    r")\b",
    re.I,
)


def is_dogfood_pilot_trust_report_freeze_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_TRUST_REPORT_FREEZE_RX.search(raw))


def parse_dogfood_pilot_trust_report_freeze_record_intent(text: str) -> tuple[str, str] | None:
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
