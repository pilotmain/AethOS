# SPDX-License-Identifier: Apache-2.0
"""FIX 179 — chat intent for frozen gate execution request adapter."""

from __future__ import annotations

import re

_FROZEN_GATE_EXECUTION_REQUEST_RX = re.compile(
    r"\b("
    r"frozen\s+gate\s+execution\s+request"
    r"|gate\s+execution\s+request"
    r"|execution\s+request\s+adapter"
    r"|show\s+execution\s+request"
    r"|frozen\s+gate\s+request"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*gate\s+(?:execution\s+)?request\s+(?P<kind>artifact|command|phrase|prerequisite|audit|forbidden|record)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "artifact": "execution_request_artifact",
    "command": "command_mapping_note",
    "phrase": "approval_phrase_note",
    "prerequisite": "prerequisite_request_note",
    "audit": "audit_link_note",
    "forbidden": "forbidden_request_note",
    "record": "frozen_gate_execution_request_record",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"enter\s+lane\s+now"
    r"|execute\s+lane\s+entry"
    r"|execute\s+gate"
    r"|execute\s+now"
    r"|run\s+workspace\s+verification"
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


def is_frozen_gate_execution_request_adapter_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_FROZEN_GATE_EXECUTION_REQUEST_RX.search(raw))


def parse_frozen_gate_execution_request_adapter_record_intent(text: str) -> tuple[str, str] | None:
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
