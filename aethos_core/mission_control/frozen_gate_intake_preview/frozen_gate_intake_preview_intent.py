# SPDX-License-Identifier: Apache-2.0
"""FIX 178 — chat intent for frozen gate intake preview."""

from __future__ import annotations

import re

_FROZEN_GATE_INTAKE_PREVIEW_RX = re.compile(
    r"\b("
    r"frozen\s+gate\s+intake\s+preview"
    r"|gate\s+intake\s+preview"
    r"|show\s+gate\s+intake"
    r"|preview\s+frozen\s+gate\s+intake"
    r"|frozen\s+gate\s+preview"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*gate\s+intake\s+(?P<kind>artifact|gate|prerequisite|command|forbidden|record)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "artifact": "intake_preview_artifact",
    "gate": "gate_match_note",
    "prerequisite": "prerequisite_note",
    "command": "intake_command_note",
    "forbidden": "forbidden_intake_note",
    "record": "frozen_gate_intake_preview_record",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"enter\s+lane\s+now"
    r"|execute\s+lane\s+entry"
    r"|execute\s+gate"
    r"|run\s+workspace\s+verification"
    r"|bypass\s+gate"
    r"|bypass\s+approval"
    r"|execute\s+now"
    r"|write\s+code"
    r"|open\s+pr"
    r"|merge\s+now"
    r"|deploy\s+now"
    r"|railway\s+mutation"
    r")\b",
    re.I,
)


def is_frozen_gate_intake_preview_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_FROZEN_GATE_INTAKE_PREVIEW_RX.search(raw))


def parse_frozen_gate_intake_preview_record_intent(text: str) -> tuple[str, str] | None:
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
