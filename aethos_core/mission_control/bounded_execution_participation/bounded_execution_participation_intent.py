# SPDX-License-Identifier: Apache-2.0
"""FIX 171 — chat intent for bounded execution participation."""

from __future__ import annotations

import re

_BOUNDED_EXECUTION_PARTICIPATION_RX = re.compile(
    r"\b("
    r"bounded\s+execution\s+participation"
    r"|execution\s+participation"
    r"|agent\s+participation"
    r"|participation\s+scope"
    r"|gate\s+routed\s+participation"
    r"|show\s+bounded\s+execution"
    r"|participate\s+in\s+mission"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*participation\s+(?P<kind>artifact|agent|gate|reengagement|forbidden|record)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "artifact": "participation_artifact",
    "agent": "agent_scope_note",
    "gate": "gate_routed_action_note",
    "reengagement": "reengagement_note",
    "forbidden": "forbidden_participation_note",
    "record": "bounded_execution_participation_record",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"autonomous\s+lane\s+entry"
    r"|bypass\s+approval"
    r"|bypass\s+gates?"
    r"|merge\s+now"
    r"|deploy\s+now"
    r"|tier\s+escalation"
    r"|participate\s+in\s+railway"
    r"|participate\s+in\s+production"
    r"|autonomous\s+execution"
    r")\b",
    re.I,
)


def is_bounded_execution_participation_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_BOUNDED_EXECUTION_PARTICIPATION_RX.search(raw))


def parse_bounded_execution_participation_record_intent(text: str) -> tuple[str, str] | None:
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
