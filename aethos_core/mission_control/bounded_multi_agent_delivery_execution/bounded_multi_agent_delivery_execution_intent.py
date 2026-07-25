# SPDX-License-Identifier: Apache-2.0
"""FIX 189 — chat intent for bounded multi-agent delivery execution."""

from __future__ import annotations

import re

_VIEW_RX = re.compile(
    r"\b("
    r"show\s+bounded\s+agent\s+delivery\s+execution"
    r"|bounded\s+multi.agent\s+delivery\s+execution"
    r"|agent\s+execution\s+packages"
    r")\b",
    re.I,
)

_RUN_PIPELINE_RX = re.compile(
    r"\brun\s+bounded\s+agent\s+delivery\s+execution\b",
    re.I,
)

_RUN_ROLE_RX = re.compile(
    r"\brun\s+bounded\s+agent\s+delivery\s+"
    r"(?P<role>planner|delivery|verification|diff\s*audit|diff_audit|risk)\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*agent\s+execution\s+(?P<kind>receipt|artifact|note)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "receipt": "agent_execution_receipt",
    "artifact": "execution_artifact",
    "note": "execution_note",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"agent\s+merge"
    r"|agent\s+deploy"
    r"|bypass\s+gate"
    r"|autonomous\s+approval"
    r")\b",
    re.I,
)

_ROLE_ALIAS: dict[str, str] = {
    "planner": "planner_agent",
    "delivery": "delivery_agent",
    "verification": "verification_agent",
    "diff audit": "diff_audit_agent",
    "diff_audit": "diff_audit_agent",
    "risk": "risk_agent",
}


def is_bounded_multi_agent_delivery_execution_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(
        _VIEW_RX.search(raw)
        or _RUN_PIPELINE_RX.search(raw)
        or _RUN_ROLE_RX.search(raw)
        or _RECORD_RX.match(raw)
    )


def parse_run_bounded_agent_delivery_execution_intent(text: str) -> str | None:
    raw = (text or "").strip()
    if _RUN_PIPELINE_RX.search(raw):
        return "__pipeline__"
    match = _RUN_ROLE_RX.search(raw)
    if not match:
        return None
    alias = (match.group("role") or "").lower().replace("_", " ")
    return _ROLE_ALIAS.get(alias.replace("  ", " "))


def parse_bounded_multi_agent_delivery_execution_record_intent(text: str) -> tuple[str, str] | None:
    raw = (text or "").strip()
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
