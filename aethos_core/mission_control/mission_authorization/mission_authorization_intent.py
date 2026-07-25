# SPDX-License-Identifier: Apache-2.0
"""FIX 170 — chat intent for mission authorization."""

from __future__ import annotations

import re

_MISSION_AUTHORIZATION_RX = re.compile(
    r"\b("
    r"mission\s+authorization"
    r"|bounded\s+work\s+envelope"
    r"|envelope\s+validation"
    r"|authorization\s+artifact"
    r"|tier\s+boundary"
    r"|gate\s+bypass"
    r"|show\s+mission\s+authorization"
    r"|authorize\s+mission"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*mission\s+(?P<kind>authorization|envelope|gate|reengagement|forbidden|record)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "authorization": "mission_authorization_artifact",
    "envelope": "envelope_scope_note",
    "gate": "gate_check_note",
    "reengagement": "reengagement_note",
    "forbidden": "forbidden_auth_note",
    "record": "mission_authorization_record",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"bypass\s+gates?"
    r"|expand\s+authority"
    r"|tier\s+escalation"
    r"|authorize\s+railway"
    r"|authorize\s+production"
    r"|autonomous\s+execution"
    r")\b",
    re.I,
)


def is_mission_authorization_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_MISSION_AUTHORIZATION_RX.search(raw))


def parse_mission_authorization_record_intent(text: str) -> tuple[str, str] | None:
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
