# SPDX-License-Identifier: Apache-2.0
"""FIX 327 — enterprise program intelligence intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_contract import (
    PROGRAM_REVIEW_RECORD_KINDS,
)
from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_store import (
    append_program_review_record,
)

_VIEW_DASHBOARD_RX = re.compile(
    r"^\s*show\s+enterprise(?:\s+program(?:\s+(?:dashboard|intelligence))?|\s+programs)?\s*$",
    re.IGNORECASE,
)
_NOTE_RX = re.compile(r"^\s*program\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*program\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_HEALTHY_RX = re.compile(r"\bwhich programs are healthy\b", re.I)
_BLOCKED_RX = re.compile(r"\bwhich programs are blocked\b", re.I)
_DEPS_RX = re.compile(r"\bwhat dependencies exist\b", re.I)
_VALUE_RX = re.compile(r"\bwhich programs create the most strategic value\b", re.I)
_RISK_RX = re.compile(r"\bwhich programs are at risk\b", re.I)
_INTERVENE_RX = re.compile(r"\bwhere should leadership intervene\b", re.I)


def parse_enterprise_program_intelligence_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "enterprise_program_dashboard"}

    if _HEALTHY_RX.search(text):
        return {"action": "view", "focus": "program_health_report"}

    if _BLOCKED_RX.search(text):
        return {"action": "view", "focus": "program_dependency_report"}

    if _DEPS_RX.search(text):
        return {"action": "view", "focus": "program_dependency_report"}

    if _VALUE_RX.search(text):
        return {"action": "view", "focus": "program_priority_matrix"}

    if _RISK_RX.search(text):
        return {"action": "view", "focus": "program_risk_report"}

    if _INTERVENE_RX.search(text):
        return {"action": "view", "focus": "program_priority_matrix"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"program_review_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "program_note",
            "content": note_match.group(1).strip(),
        }

    return None


def handle_enterprise_program_intelligence_intent(
    intent: dict[str, Any],
    *,
    session_id: str = "default",
) -> dict[str, Any]:
    if intent.get("action") == "record":
        kind = str(intent["kind"])
        if kind not in PROGRAM_REVIEW_RECORD_KINDS:
            raise ValueError(f"unsupported program review kind: {kind}")
        record = append_program_review_record(
            kind=kind,
            content=str(intent["content"]),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
        )
        return {"action": "record", "record": record}
    return {"action": "view", "focus": str(intent.get("focus") or "enterprise_program_dashboard")}
