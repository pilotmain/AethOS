# SPDX-License-Identifier: Apache-2.0
"""FIX 183 — chat intent for pilot validation trust board."""

from __future__ import annotations

import re

_VALIDATION_BOARD_RX = re.compile(
    r"\b("
    r"pilot\s+validation"
    r"|pilot\s+trust\s+board"
    r"|show\s+pilot\s+validation"
    r"|pilot\s+results\s+board"
    r"|trust\s+recommendation"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*validation\s+(?P<kind>artifact|trust|effort|record)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "artifact": "validation_artifact",
    "trust": "trust_note",
    "effort": "operator_effort_note",
    "record": "validation_record",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"run\s+pilot"
    r"|rerun\s+pilot"
    r"|re-?execute\s+pilot"
    r"|bypass\s+gate"
    r"|direct\s+provider"
    r"|hidden\s+execute"
    r")\b",
    re.I,
)


def is_pilot_validation_trust_board_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_VALIDATION_BOARD_RX.search(raw))


def parse_pilot_validation_trust_board_record_intent(text: str) -> tuple[str, str] | None:
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
