# SPDX-License-Identifier: Apache-2.0
"""FIX 177 — chat intent for gate-routed lane entry handoff."""

from __future__ import annotations

import re

_GATE_ROUTED_LANE_ENTRY_HANDOFF_RX = re.compile(
    r"\b("
    r"gate.?routed\s+lane\s+entry\s+handoff"
    r"|lane\s+entry\s+handoff"
    r"|gate\s+handoff\s+packet"
    r"|show\s+gate\s+handoff"
    r"|frozen\s+gate\s+handoff"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*gate\s+handoff\s+(?P<kind>artifact|gate|validation|command|forbidden|record)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "artifact": "gate_handoff_artifact",
    "gate": "target_gate_note",
    "validation": "validation_requirement_note",
    "command": "handoff_command_note",
    "forbidden": "forbidden_handoff_note",
    "record": "gate_routed_lane_entry_handoff_record",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"enter\s+lane\s+now"
    r"|execute\s+lane\s+entry"
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


def is_gate_routed_lane_entry_handoff_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_GATE_ROUTED_LANE_ENTRY_HANDOFF_RX.search(raw))


def parse_gate_routed_lane_entry_handoff_record_intent(text: str) -> tuple[str, str] | None:
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
