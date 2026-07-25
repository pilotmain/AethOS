# SPDX-License-Identifier: Apache-2.0
"""FIX 326 — strategic planning intelligence intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_contract import (
    PLANNING_REVIEW_RECORD_KINDS,
)
from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_store import (
    append_planning_review_record,
)

_VIEW_DASHBOARD_RX = re.compile(
    r"^\s*show\s+strategic(?:\s+planning(?:\s+(?:dashboard|intelligence))?|\s+plan(?:\s+dashboard)?)?\s*$",
    re.IGNORECASE,
)
_NOTE_RX = re.compile(r"^\s*planning\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*planning\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_PATHS_RX = re.compile(r"\bwhat strategic paths exist\b", re.I)
_TRADEOFF_RX = re.compile(r"\bwhat are the trade-offs\b", re.I)
_RISK_RX = re.compile(r"\bwhat are the risks\b", re.I)
_OPP_RX = re.compile(r"\bwhat are the opportunities\b", re.I)
_SCENARIO_RX = re.compile(r"\bwhat happens under different scenarios\b", re.I)
_STRONGEST_RX = re.compile(r"\bwhich plans appear strongest\b", re.I)


def parse_strategic_planning_intelligence_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "strategic_planning_dashboard"}

    if _PATHS_RX.search(text):
        return {"action": "view", "focus": "strategic_scenario_report"}

    if _TRADEOFF_RX.search(text):
        return {"action": "view", "focus": "strategic_comparison_matrix"}

    if _RISK_RX.search(text):
        return {"action": "view", "focus": "strategic_risk_forecast"}

    if _OPP_RX.search(text):
        return {"action": "view", "focus": "strategic_opportunity_forecast"}

    if _SCENARIO_RX.search(text):
        return {"action": "view", "focus": "scenario_impact_report"}

    if _STRONGEST_RX.search(text):
        return {"action": "view", "focus": "strategic_comparison_matrix"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"planning_review_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "planning_note",
            "content": note_match.group(1).strip(),
        }

    return None


def handle_strategic_planning_intelligence_intent(
    intent: dict[str, Any],
    *,
    session_id: str = "default",
) -> dict[str, Any]:
    if intent.get("action") == "record":
        kind = str(intent["kind"])
        if kind not in PLANNING_REVIEW_RECORD_KINDS:
            raise ValueError(f"unsupported planning review kind: {kind}")
        record = append_planning_review_record(
            kind=kind,
            content=str(intent["content"]),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
        )
        return {"action": "record", "record": record}
    return {"action": "view", "focus": str(intent.get("focus") or "strategic_planning_dashboard")}
