# SPDX-License-Identifier: Apache-2.0
"""FIX 325 — executive decision intelligence intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_contract import (
    EXECUTIVE_REVIEW_RECORD_KINDS,
)
from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_store import (
    append_executive_review_record,
)

_VIEW_DASHBOARD_RX = re.compile(
    r"^\s*show\s+executive(?:\s+decision(?:\s+(?:dashboard|intelligence))?|\s+dashboard|\s+intelligence)?\s*$",
    re.IGNORECASE,
)
_NOTE_RX = re.compile(r"^\s*executive\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*executive\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_FOCUS_RX = re.compile(r"\bwhat should leadership focus on next\b", re.I)
_URGENT_RX = re.compile(r"\bwhat decisions are most urgent\b", re.I)
_RISK_RX = re.compile(r"\bwhat decisions carry the highest risk\b", re.I)
_ACCEL_RX = re.compile(r"\bwhat opportunities deserve acceleration\b", re.I)
_DEFER_RX = re.compile(r"\bwhat should be deferred\b", re.I)


def parse_executive_decision_intelligence_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "executive_decision_dashboard"}

    if _FOCUS_RX.search(text):
        return {"action": "view", "focus": "executive_recommendation_report"}

    if _URGENT_RX.search(text):
        return {"action": "view", "focus": "decision_opportunity_report"}

    if _RISK_RX.search(text):
        return {"action": "view", "focus": "decision_risk_report"}

    if _ACCEL_RX.search(text):
        return {"action": "view", "focus": "executive_priority_matrix"}

    if _DEFER_RX.search(text):
        return {"action": "view", "focus": "tradeoff_analysis_report"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"executive_review_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "executive_note",
            "content": note_match.group(1).strip(),
        }

    return None


def handle_executive_decision_intelligence_intent(
    intent: dict[str, Any],
    *,
    session_id: str = "default",
) -> dict[str, Any]:
    if intent.get("action") == "record":
        kind = str(intent["kind"])
        if kind not in EXECUTIVE_REVIEW_RECORD_KINDS:
            raise ValueError(f"unsupported executive review kind: {kind}")
        record = append_executive_review_record(
            kind=kind,
            content=str(intent["content"]),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
        )
        return {"action": "record", "record": record}
    return {"action": "view", "focus": str(intent.get("focus") or "executive_decision_dashboard")}
