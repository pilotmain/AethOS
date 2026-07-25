# SPDX-License-Identifier: Apache-2.0
"""FIX 318 — product analytics intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_contract import (
    ANALYTICS_REVIEW_RECORD_KINDS,
)
from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_store import (
    append_analytics_review_record,
)

_VIEW_DASHBOARD_RX = re.compile(
    r"^\s*show\s+(?:product\s+)?analytics(?:\s+dashboard|\s+foundation)?\s*$",
    re.IGNORECASE,
)
_NOTE_RX = re.compile(r"^\s*analytics\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*analytics\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_ONBOARDING_COMPLETE_RX = re.compile(r"\bhow many users complete onboarding\b", re.I)
_DROP_OFF_RX = re.compile(r"\bwhere do users drop off\b", re.I)
_PROVIDERS_RX = re.compile(r"\bwhich providers are most connected\b", re.I)
_CAPABILITIES_RX = re.compile(r"\bwhich capabilities are most used\b", re.I)
_PLANS_RX = re.compile(r"\bwhich plans are most successful\b", re.I)
_SUCCESS_BEHAVIOR_RX = re.compile(r"\bwhich behaviors predict success\b", re.I)


def parse_product_analytics_foundation_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "analytics_dashboard"}

    if _ONBOARDING_COMPLETE_RX.search(text):
        return {"action": "view", "focus": "onboarding_analytics_report"}

    if _DROP_OFF_RX.search(text):
        return {"action": "view", "focus": "onboarding_analytics_report"}

    if _PROVIDERS_RX.search(text):
        return {"action": "view", "focus": "provider_analytics_report"}

    if _CAPABILITIES_RX.search(text):
        return {"action": "view", "focus": "capability_usage_report"}

    if _PLANS_RX.search(text):
        return {"action": "view", "focus": "commercial_analytics_report"}

    if _SUCCESS_BEHAVIOR_RX.search(text):
        return {"action": "view", "focus": "user_journey_report"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"analytics_review_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "analytics_note",
            "content": note_match.group(1).strip(),
        }

    return None


def handle_product_analytics_foundation_intent(
    intent: dict[str, Any],
    *,
    session_id: str = "default",
) -> dict[str, Any]:
    if intent.get("action") == "record":
        kind = str(intent["kind"])
        if kind not in ANALYTICS_REVIEW_RECORD_KINDS:
            raise ValueError(f"unsupported analytics review kind: {kind}")
        record = append_analytics_review_record(
            kind=kind,
            content=str(intent["content"]),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
        )
        return {"action": "record", "record": record}
    return {"action": "view", "focus": str(intent.get("focus") or "analytics_dashboard")}
