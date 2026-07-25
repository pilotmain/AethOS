# SPDX-License-Identifier: Apache-2.0
"""FIX 324 — strategic portfolio intelligence intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_contract import (
    STRATEGIC_REVIEW_RECORD_KINDS,
)
from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_store import (
    append_strategic_review_record,
)

_VIEW_DASHBOARD_RX = re.compile(
    r"^\s*show\s+strategic\s+portfolio(?:\s+dashboard|\s+intelligence)?\s*$",
    re.IGNORECASE,
)
_NOTE_RX = re.compile(r"^\s*strategic\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*strategic\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_VALUE_RX = re.compile(r"\bwhich products create the most value\b", re.I)
_INVEST_RX = re.compile(r"\bwhich initiatives deserve investment\b", re.I)
_RISK_RX = re.compile(r"\bwhere are the highest risks\b", re.I)
_ROI_RX = re.compile(r"\bwhere are the highest roi opportunities\b", re.I)
_ALIGN_RX = re.compile(r"\bwhich efforts align best with strategy\b", re.I)


def parse_strategic_portfolio_intelligence_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "strategic_portfolio_dashboard"}

    if _VALUE_RX.search(text):
        return {"action": "view", "focus": "strategic_value_report"}

    if _INVEST_RX.search(text):
        return {"action": "view", "focus": "investment_opportunity_report"}

    if _RISK_RX.search(text):
        return {"action": "view", "focus": "portfolio_risk_report"}

    if _ROI_RX.search(text):
        return {"action": "view", "focus": "strategic_priority_matrix"}

    if _ALIGN_RX.search(text):
        return {"action": "view", "focus": "strategic_alignment_report"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"strategic_review_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "strategic_note",
            "content": note_match.group(1).strip(),
        }

    return None


def handle_strategic_portfolio_intelligence_intent(
    intent: dict[str, Any],
    *,
    session_id: str = "default",
) -> dict[str, Any]:
    if intent.get("action") == "record":
        kind = str(intent["kind"])
        if kind not in STRATEGIC_REVIEW_RECORD_KINDS:
            raise ValueError(f"unsupported strategic review kind: {kind}")
        record = append_strategic_review_record(
            kind=kind,
            content=str(intent["content"]),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
        )
        return {"action": "record", "record": record}
    return {"action": "view", "focus": str(intent.get("focus") or "strategic_portfolio_dashboard")}
