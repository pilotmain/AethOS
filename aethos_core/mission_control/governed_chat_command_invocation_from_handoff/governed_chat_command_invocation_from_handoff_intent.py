# SPDX-License-Identifier: Apache-2.0
"""FIX 180 — chat intent for governed chat command invocation from handoff."""

from __future__ import annotations

import re

_GOVERNED_CHAT_COMMAND_INVOCATION_RX = re.compile(
    r"\b("
    r"governed\s+chat\s+command\s+invocation"
    r"|handoff\s+command\s+invocation"
    r"|governed\s+handoff\s+invocation"
    r"|show\s+handoff\s+invocation"
    r"|handoff\s+invocation\s+packet"
    r")\b",
    re.I,
)

_INVOKE_RX = re.compile(
    r"^\s*invoke\s+handoff\s+command\s*$",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*handoff\s+invocation\s+(?P<kind>artifact|command|origin|audit|forbidden|record)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "artifact": "invocation_artifact",
    "command": "chat_command_note",
    "origin": "origin_log_note",
    "audit": "audit_link_note",
    "forbidden": "forbidden_invocation_note",
    "record": "governed_chat_command_invocation_record",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"bypass\s+gate"
    r"|bypass\s+approval"
    r"|direct\s+provider"
    r"|direct\s+api"
    r"|hidden\s+execute"
    r"|autonomous\s+invoke"
    r"|railway\s+mutation"
    r"|merge\s+now"
    r"|deploy\s+now"
    r")\b",
    re.I,
)


def is_governed_chat_command_invocation_from_handoff_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_GOVERNED_CHAT_COMMAND_INVOCATION_RX.search(raw))


def is_invoke_handoff_command_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw or _FORBIDDEN_RX.search(raw):
        return False
    return bool(_INVOKE_RX.match(raw))


def parse_governed_chat_command_invocation_from_handoff_record_intent(text: str) -> tuple[str, str] | None:
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
