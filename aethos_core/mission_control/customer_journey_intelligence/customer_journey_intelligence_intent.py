# SPDX-License-Identifier: Apache-2.0
"""FIX 321 — customer journey intelligence intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_contract import (
    JOURNEY_REVIEW_RECORD_KINDS,
)
from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_store import (
    append_journey_review_record,
)

_VIEW_DASHBOARD_RX = re.compile(
    r"^\s*show\s+(?:customer\s+)?journey(?:\s+dashboard|\s+intelligence)?\s*$",
    re.IGNORECASE,
)
_NOTE_RX = re.compile(r"^\s*journey\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*journey\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_DROPOFF_RX = re.compile(r"\bwhere do customers drop off\b", re.I)
_SUCCESS_RX = re.compile(r"\bwhat journeys lead to success\b", re.I)
_ONBOARDING_RX = re.compile(r"\bwhat onboarding paths perform best\b", re.I)
_COHORT_RX = re.compile(r"\bwhich cohorts retain best\b", re.I)
_EXPANSION_RX = re.compile(r"\bwhich journeys lead to expansion\b", re.I)
_IMPROVE_RX = re.compile(r"\bwhat should improve in the customer journey\b", re.I)


def parse_customer_journey_intelligence_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "customer_journey_dashboard"}

    if _DROPOFF_RX.search(text):
        return {"action": "view", "focus": "journey_dropoff_report"}

    if _SUCCESS_RX.search(text):
        return {"action": "view", "focus": "journey_success_report"}

    if _ONBOARDING_RX.search(text):
        return {"action": "view", "focus": "journey_friction_report"}

    if _COHORT_RX.search(text):
        return {"action": "view", "focus": "journey_cohort_report"}

    if _EXPANSION_RX.search(text):
        return {"action": "view", "focus": "journey_success_report"}

    if _IMPROVE_RX.search(text):
        return {"action": "view", "focus": "journey_priority_matrix"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"journey_review_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "journey_note",
            "content": note_match.group(1).strip(),
        }

    return None


def handle_customer_journey_intelligence_intent(
    intent: dict[str, Any],
    *,
    session_id: str = "default",
) -> dict[str, Any]:
    if intent.get("action") == "record":
        kind = str(intent["kind"])
        if kind not in JOURNEY_REVIEW_RECORD_KINDS:
            raise ValueError(f"unsupported journey review kind: {kind}")
        record = append_journey_review_record(
            kind=kind,
            content=str(intent["content"]),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
        )
        return {"action": "record", "record": record}
    return {"action": "view", "focus": str(intent.get("focus") or "customer_journey_dashboard")}
