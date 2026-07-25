# SPDX-License-Identifier: Apache-2.0
"""FIX 328 — organizational effectiveness intelligence intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_contract import (
    ORGANIZATIONAL_REVIEW_RECORD_KINDS,
)
from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_store import (
    append_organizational_review_record,
)

_VIEW_DASHBOARD_RX = re.compile(
    r"^\s*show\s+organizational(?:\s+effectiveness(?:\s+(?:dashboard|intelligence))?|\s+dashboard)?\s*$",
    re.IGNORECASE,
)
_NOTE_RX = re.compile(r"^\s*organization\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*organization\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_FRICTION_RX = re.compile(r"\bwhere is organizational friction\b", re.I)
_BOTTLENECK_RX = re.compile(r"\bwhere are governance bottlenecks\b", re.I)
_COORD_RX = re.compile(r"\bwhere are coordination failures\b", re.I)
_CAPACITY_RX = re.compile(r"\bwhere is capacity constrained\b", re.I)
_EFFECTIVE_RX = re.compile(r"\bhow effective is execution\b", re.I)


def parse_organizational_effectiveness_intelligence_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "organizational_effectiveness_dashboard"}

    if _FRICTION_RX.search(text):
        return {"action": "view", "focus": "governance_friction_report"}

    if _BOTTLENECK_RX.search(text):
        return {"action": "view", "focus": "governance_friction_report"}

    if _COORD_RX.search(text):
        return {"action": "view", "focus": "coordination_intelligence_report"}

    if _CAPACITY_RX.search(text):
        return {"action": "view", "focus": "organizational_capacity_report"}

    if _EFFECTIVE_RX.search(text):
        return {"action": "view", "focus": "organizational_effectiveness_scorecard"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"organization_review_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "organization_note",
            "content": note_match.group(1).strip(),
        }

    return None


def handle_organizational_effectiveness_intelligence_intent(
    intent: dict[str, Any],
    *,
    session_id: str = "default",
) -> dict[str, Any]:
    if intent.get("action") == "record":
        kind = str(intent["kind"])
        if kind not in ORGANIZATIONAL_REVIEW_RECORD_KINDS:
            raise ValueError(f"unsupported organizational review kind: {kind}")
        record = append_organizational_review_record(
            kind=kind,
            content=str(intent["content"]),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
        )
        return {"action": "record", "record": record}
    return {"action": "view", "focus": str(intent.get("focus") or "organizational_effectiveness_dashboard")}
