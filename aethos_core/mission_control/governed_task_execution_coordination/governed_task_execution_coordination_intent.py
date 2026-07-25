# SPDX-License-Identifier: Apache-2.0
"""FIX 172 — chat intent for governed task execution coordination."""

from __future__ import annotations

import re

_GOVERNED_TASK_EXECUTION_COORDINATION_RX = re.compile(
    r"\b("
    r"governed\s+task\s+execution\s+coordination"
    r"|task\s+execution\s+coordination"
    r"|execution\s+coordination"
    r"|package\s+lifecycle"
    r"|package\s+sequencing"
    r"|coordinate\s+packages"
    r"|show\s+execution\s+coordination"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*coordination\s+(?P<kind>artifact|assignment|lifecycle|dependency|escalation|forbidden|record)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "artifact": "coordination_artifact",
    "assignment": "package_assignment_note",
    "lifecycle": "lifecycle_note",
    "dependency": "dependency_note",
    "escalation": "escalation_note",
    "forbidden": "forbidden_coordination_note",
    "record": "governed_task_execution_coordination_record",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"execute\s+now"
    r"|perform\s+execution"
    r"|bypass\s+gates?"
    r"|autonomous\s+lane\s+entry"
    r"|merge\s+now"
    r"|deploy\s+now"
    r"|write\s+code\s+now"
    r"|open\s+pr\s+now"
    r")\b",
    re.I,
)


def is_governed_task_execution_coordination_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_GOVERNED_TASK_EXECUTION_COORDINATION_RX.search(raw))


def parse_governed_task_execution_coordination_record_intent(text: str) -> tuple[str, str] | None:
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
