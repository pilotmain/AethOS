# SPDX-License-Identifier: Apache-2.0
"""FIX 330 — executive operating system dashboard intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_contract import (
    DASHBOARD_RECORD_KINDS,
)
from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_store import (
    append_dashboard_review_record,
)

_VIEW_DASHBOARD_RX = re.compile(
    r"^\s*show\s+(?:executive\s+)?(?:operating\s+system\s+)?dashboard\s*$",
    re.IGNORECASE,
)
_NOTE_RX = re.compile(r"^\s*dashboard\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*dashboard\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_BUSINESS_RX = re.compile(r"\bhow is the business doing\b", re.I)
_CUSTOMERS_RX = re.compile(r"\bhow are customers doing\b", re.I)
_PROGRAMS_RX = re.compile(r"\bhow are programs doing\b", re.I)
_OPERATIONS_RX = re.compile(r"\bhow are operations doing\b", re.I)
_ATTENTION_RX = re.compile(r"\bwhat requires executive attention\b", re.I)


def parse_executive_operating_system_dashboard_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "executive_operating_system_dashboard"}

    if _BUSINESS_RX.search(text):
        return {"action": "view", "focus": "executive_summary_panel"}

    if _CUSTOMERS_RX.search(text):
        return {"action": "view", "focus": "customer_panel"}

    if _PROGRAMS_RX.search(text):
        return {"action": "view", "focus": "program_panel"}

    if _OPERATIONS_RX.search(text):
        return {"action": "view", "focus": "operations_panel"}

    if _ATTENTION_RX.search(text):
        return {"action": "view", "focus": "executive_operating_system_dashboard"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"dashboard_review_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "dashboard_note",
            "content": note_match.group(1).strip(),
        }

    return None


def handle_executive_operating_system_dashboard_intent(
    intent: dict[str, Any],
    *,
    session_id: str = "default",
) -> dict[str, Any]:
    if intent.get("action") == "record":
        kind = str(intent["kind"])
        if kind not in DASHBOARD_RECORD_KINDS:
            raise ValueError(f"unsupported dashboard review kind: {kind}")
        record = append_dashboard_review_record(
            kind=kind,
            content=str(intent["content"]),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
        )
        return {"action": "record", "record": record}
    return {"action": "view", "focus": str(intent.get("focus") or "executive_operating_system_dashboard")}
