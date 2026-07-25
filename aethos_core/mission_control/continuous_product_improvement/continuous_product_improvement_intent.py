# SPDX-License-Identifier: Apache-2.0
"""FIX 317 — continuous product improvement intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_contract import (
    IMPROVEMENT_REVIEW_RECORD_KINDS,
)
from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_store import (
    append_improvement_review_record,
)

_VIEW_DASHBOARD_RX = re.compile(
    r"^\s*show\s+(?:continuous\s+)?improvement(?:\s+dashboard|\s+program)?\s*$",
    re.IGNORECASE,
)
_NOTE_RX = re.compile(r"^\s*improvement\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*improvement\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_WHAT_IMPROVE_RX = re.compile(r"\bwhat\s+should\s+improve\s+next\b", re.I)
_USERS_STRUGGLING_RX = re.compile(r"\bwhat\s+are\s+users\s+struggling\s+with\b", re.I)
_ONBOARDING_FAIL_RX = re.compile(r"\bwhere\s+is\s+onboarding\s+failing\b", re.I)
_OPS_REPEAT_RX = re.compile(r"\bwhat\s+operational\s+issues\s+repeat\b", re.I)
_COMMERCIAL_FRICTION_RX = re.compile(r"\bwhat\s+commercial\s+friction\s+exists\b", re.I)
_HIGHEST_ROI_RX = re.compile(r"\bwhat\s+improvements\s+have\s+the\s+highest\s+roi\b", re.I)


def parse_continuous_product_improvement_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "continuous_improvement_dashboard"}

    if _WHAT_IMPROVE_RX.search(text) or _HIGHEST_ROI_RX.search(text):
        return {"action": "view", "focus": "improvement_priority_matrix"}

    if _USERS_STRUGGLING_RX.search(text):
        return {"action": "view", "focus": "feedback_intelligence_report"}

    if _ONBOARDING_FAIL_RX.search(text):
        return {"action": "view", "focus": "onboarding_improvement_report"}

    if _OPS_REPEAT_RX.search(text):
        return {"action": "view", "focus": "operational_improvement_report"}

    if _COMMERCIAL_FRICTION_RX.search(text):
        return {"action": "view", "focus": "commercial_improvement_report"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"improvement_review_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "improvement_note",
            "content": note_match.group(1).strip(),
        }

    return None


def handle_continuous_product_improvement_intent(
    intent: dict[str, Any],
    *,
    session_id: str = "default",
) -> dict[str, Any]:
    if intent.get("action") == "record":
        kind = str(intent["kind"])
        if kind not in IMPROVEMENT_REVIEW_RECORD_KINDS:
            raise ValueError(f"unsupported improvement review kind: {kind}")
        record = append_improvement_review_record(
            kind=kind,
            content=str(intent["content"]),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
        )
        return {"action": "record", "record": record}
    return {"action": "view", "focus": str(intent.get("focus") or "continuous_improvement_dashboard")}
