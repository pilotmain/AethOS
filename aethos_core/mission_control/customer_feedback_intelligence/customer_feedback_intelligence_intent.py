# SPDX-License-Identifier: Apache-2.0
"""FIX 319 — customer feedback intelligence intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_contract import (
    FEEDBACK_REVIEW_RECORD_KINDS,
)
from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_store import (
    append_feedback_review_record,
)

_VIEW_DASHBOARD_RX = re.compile(
    r"^\s*show\s+(?:customer\s+)?feedback(?:\s+dashboard|\s+intelligence)?\s*$",
    re.IGNORECASE,
)
_NOTE_RX = re.compile(r"^\s*feedback\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*feedback\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_ASKING_RX = re.compile(r"\bwhat are customers asking for\b", re.I)
_COMPLAINTS_RX = re.compile(r"\bwhat complaints appear repeatedly\b", re.I)
_TRENDS_RX = re.compile(r"\bwhich feedback trends are emerging\b", re.I)
_GAPS_RX = re.compile(r"\bwhat capability gaps exist\b", re.I)
_FRICTION_RX = re.compile(r"\bwhat friction points are most common\b", re.I)
_NEXT_RX = re.compile(r"\bwhat should the team consider improving next\b", re.I)


def parse_customer_feedback_intelligence_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "customer_feedback_dashboard"}

    if _ASKING_RX.search(text):
        return {"action": "view", "focus": "feedback_trend_report"}

    if _COMPLAINTS_RX.search(text):
        return {"action": "view", "focus": "feedback_trend_report"}

    if _TRENDS_RX.search(text):
        return {"action": "view", "focus": "feedback_trend_report"}

    if _GAPS_RX.search(text):
        return {"action": "view", "focus": "capability_gap_report"}

    if _FRICTION_RX.search(text):
        return {"action": "view", "focus": "customer_friction_report"}

    if _NEXT_RX.search(text):
        return {"action": "view", "focus": "feedback_priority_matrix"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"feedback_review_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "feedback_note",
            "content": note_match.group(1).strip(),
        }

    return None


def handle_customer_feedback_intelligence_intent(
    intent: dict[str, Any],
    *,
    session_id: str = "default",
) -> dict[str, Any]:
    if intent.get("action") == "record":
        kind = str(intent["kind"])
        if kind not in FEEDBACK_REVIEW_RECORD_KINDS:
            raise ValueError(f"unsupported feedback review kind: {kind}")
        record = append_feedback_review_record(
            kind=kind,
            content=str(intent["content"]),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
        )
        return {"action": "record", "record": record}
    return {"action": "view", "focus": str(intent.get("focus") or "customer_feedback_dashboard")}
