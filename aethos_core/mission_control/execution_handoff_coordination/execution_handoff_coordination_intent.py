# SPDX-License-Identifier: Apache-2.0
"""FIX 167 — chat intent for execution handoff coordination."""

from __future__ import annotations

import re

_EXECUTION_HANDOFF_RX = re.compile(
    r"\b("
    r"execution\s+handoff"
    r"|handoff\s+coordination"
    r"|governed\s+execution\s+handoff"
    r"|eligible\s+lanes?"
    r"|handoff\s+package"
    r"|required\s+lane\s+gates?"
    r"|next[\-\s]step\s+command"
    r"|forbidden\s+actions?"
    r"|handoff\s+integrity"
    r"|show\s+execution\s+handoff"
    r"|show\s+handoff"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*handoff\s+(?P<kind>artifact|gate|approval|blocker|forbidden|step|record)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "artifact": "handoff_artifact",
    "gate": "lane_gate_note",
    "approval": "approval_requirement_note",
    "blocker": "blocker_note",
    "forbidden": "forbidden_action_note",
    "step": "next_step_note",
    "record": "handoff_coordination_record",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"autonomous\s+execution"
    r"|autonomous\s+approval"
    r"|autonomous\s+lane\s+entry"
    r"|open\s+pr"
    r"|merge\s+deploy"
    r"|mutate\s+railway"
    r"|execute\s+handoff\s+autonomously"
    r")\b",
    re.I,
)


def is_execution_handoff_coordination_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_EXECUTION_HANDOFF_RX.search(raw))


def parse_handoff_record_intent(text: str) -> tuple[str, str] | None:
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
