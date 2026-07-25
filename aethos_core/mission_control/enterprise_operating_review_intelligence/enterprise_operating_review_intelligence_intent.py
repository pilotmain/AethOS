# SPDX-License-Identifier: Apache-2.0
"""FIX 329 — enterprise operating review intelligence intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_contract import (
    OPERATING_REVIEW_RECORD_KINDS,
)
from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_store import (
    append_operating_review_record,
)

_VIEW_DASHBOARD_RX = re.compile(
    r"^\s*show\s+(?:enterprise\s+)?operating(?:\s+review(?:\s+(?:dashboard|intelligence))?|\s+dashboard)?\s*$",
    re.IGNORECASE,
)
_NOTE_RX = re.compile(r"^\s*operating\s+review\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*operating\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_STATE_RX = re.compile(r"\bwhat is the current state of the organization\b", re.I)
_RISK_RX = re.compile(r"\bwhat are the biggest risks\b", re.I)
_OPP_RX = re.compile(r"\bwhat are the biggest opportunities\b", re.I)
_ATTENTION_RX = re.compile(r"\bwhat requires executive attention\b", re.I)
_EXECUTION_RX = re.compile(r"\bhow healthy is execution\b", re.I)


def parse_enterprise_operating_review_intelligence_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "enterprise_operating_dashboard"}

    if _STATE_RX.search(text):
        return {"action": "view", "focus": "executive_operating_snapshot"}

    if _RISK_RX.search(text):
        return {"action": "view", "focus": "enterprise_risk_review"}

    if _OPP_RX.search(text):
        return {"action": "view", "focus": "enterprise_opportunity_review"}

    if _ATTENTION_RX.search(text):
        return {"action": "view", "focus": "executive_action_registry"}

    if _EXECUTION_RX.search(text):
        return {"action": "view", "focus": "executive_operating_scorecard"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"operating_review_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "operating_review_note",
            "content": note_match.group(1).strip(),
        }

    return None


def handle_enterprise_operating_review_intelligence_intent(
    intent: dict[str, Any],
    *,
    session_id: str = "default",
) -> dict[str, Any]:
    if intent.get("action") == "record":
        kind = str(intent["kind"])
        if kind not in OPERATING_REVIEW_RECORD_KINDS:
            raise ValueError(f"unsupported operating review kind: {kind}")
        record = append_operating_review_record(
            kind=kind,
            content=str(intent["content"]),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
        )
        return {"action": "record", "record": record}
    return {"action": "view", "focus": str(intent.get("focus") or "enterprise_operating_dashboard")}
