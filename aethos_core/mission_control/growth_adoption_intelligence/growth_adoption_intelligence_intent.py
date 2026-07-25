# SPDX-License-Identifier: Apache-2.0
"""FIX 320 — growth & adoption intelligence intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_contract import (
    GROWTH_REVIEW_RECORD_KINDS,
)
from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_store import (
    append_growth_review_record,
)

_VIEW_DASHBOARD_RX = re.compile(
    r"^\s*show\s+(?:growth|adoption)(?:\s+(?:and\s+)?adoption)?(?:\s+dashboard|\s+intelligence)?\s*$",
    re.IGNORECASE,
)
_NOTE_RX = re.compile(r"^\s*growth\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*growth\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_ADOPTING_RX = re.compile(r"\bwhich customers are adopting successfully\b", re.I)
_AT_RISK_RX = re.compile(r"\bwhich customers are at risk\b", re.I)
_RETENTION_RX = re.compile(r"\bwhich behaviors predict retention\b", re.I)
_PROVIDERS_RX = re.compile(r"\bwhich providers drive adoption\b", re.I)
_EXPANSION_RX = re.compile(r"\bwhere are expansion opportunities\b", re.I)
_ROI_RX = re.compile(r"\bwhat growth opportunities have the highest roi\b", re.I)


def parse_growth_adoption_intelligence_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "growth_adoption_dashboard"}

    if _ADOPTING_RX.search(text):
        return {"action": "view", "focus": "adoption_registry"}

    if _AT_RISK_RX.search(text):
        return {"action": "view", "focus": "churn_risk_report"}

    if _RETENTION_RX.search(text):
        return {"action": "view", "focus": "success_pattern_report"}

    if _PROVIDERS_RX.search(text):
        return {"action": "view", "focus": "adoption_analytics_report"}

    if _EXPANSION_RX.search(text):
        return {"action": "view", "focus": "expansion_intelligence_report"}

    if _ROI_RX.search(text):
        return {"action": "view", "focus": "growth_priority_matrix"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"growth_review_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "growth_note",
            "content": note_match.group(1).strip(),
        }

    return None


def handle_growth_adoption_intelligence_intent(
    intent: dict[str, Any],
    *,
    session_id: str = "default",
) -> dict[str, Any]:
    if intent.get("action") == "record":
        kind = str(intent["kind"])
        if kind not in GROWTH_REVIEW_RECORD_KINDS:
            raise ValueError(f"unsupported growth review kind: {kind}")
        record = append_growth_review_record(
            kind=kind,
            content=str(intent["content"]),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
        )
        return {"action": "record", "record": record}
    return {"action": "view", "focus": str(intent.get("focus") or "growth_adoption_dashboard")}
