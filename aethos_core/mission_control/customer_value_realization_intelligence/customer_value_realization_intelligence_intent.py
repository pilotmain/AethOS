# SPDX-License-Identifier: Apache-2.0
"""FIX 323 — customer value realization intelligence intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_contract import (
    VALUE_REVIEW_RECORD_KINDS,
)
from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_store import (
    append_value_review_record,
)

_VIEW_DASHBOARD_RX = re.compile(
    r"^\s*show\s+(?:customer\s+)?value(?:\s+dashboard|\s+realization(?:\s+intelligence)?)?\s*$",
    re.IGNORECASE,
)
_NOTE_RX = re.compile(r"^\s*value\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*value\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_REALIZING_RX = re.compile(r"\bwhat value are customers realizing\b", re.I)
_UNREALIZED_RX = re.compile(r"\bwhat value remains unrealized\b", re.I)
_CAP_VALUE_RX = re.compile(r"\bwhich capabilities create the most value\b", re.I)
_JOURNEY_VALUE_RX = re.compile(r"\bwhich journeys create the most value\b", re.I)
_GAPS_RX = re.compile(r"\bwhere are customer value gaps\b", re.I)
_GOALS_RX = re.compile(r"\bhow effectively are customer goals being achieved\b", re.I)


def parse_customer_value_realization_intelligence_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "customer_value_dashboard"}

    if _REALIZING_RX.search(text):
        return {"action": "view", "focus": "value_outcome_registry"}

    if _UNREALIZED_RX.search(text):
        return {"action": "view", "focus": "value_gap_report"}

    if _CAP_VALUE_RX.search(text):
        return {"action": "view", "focus": "capability_value_report"}

    if _JOURNEY_VALUE_RX.search(text):
        return {"action": "view", "focus": "journey_value_report"}

    if _GAPS_RX.search(text):
        return {"action": "view", "focus": "value_gap_report"}

    if _GOALS_RX.search(text):
        return {"action": "view", "focus": "customer_success_outcome_report"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"value_review_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "value_note",
            "content": note_match.group(1).strip(),
        }

    return None


def handle_customer_value_realization_intelligence_intent(
    intent: dict[str, Any],
    *,
    session_id: str = "default",
) -> dict[str, Any]:
    if intent.get("action") == "record":
        kind = str(intent["kind"])
        if kind not in VALUE_REVIEW_RECORD_KINDS:
            raise ValueError(f"unsupported value review kind: {kind}")
        record = append_value_review_record(
            kind=kind,
            content=str(intent["content"]),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
        )
        return {"action": "record", "record": record}
    return {"action": "view", "focus": str(intent.get("focus") or "customer_value_dashboard")}
