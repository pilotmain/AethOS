# SPDX-License-Identifier: Apache-2.0
"""FIX 313 — launch operations center intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.launch_operations_center.launch_operations_center_contract import (
    LAUNCH_OPERATIONS_CENTER_RECORD_KINDS,
)
from aethos_core.mission_control.launch_operations_center.launch_operations_center_store import (
    append_launch_operations_center_record,
)

_VIEW_OPS_RX = re.compile(r"^\s*show\s+launch\s+operations\s*$", re.IGNORECASE)
_VIEW_STATUS_RX = re.compile(r"^\s*show\s+launch\s+status\s*$", re.IGNORECASE)
_VIEW_BLOCKERS_RX = re.compile(r"^\s*show\s+launch\s+blockers\s*$", re.IGNORECASE)
_VIEW_RISKS_RX = re.compile(r"^\s*show\s+launch\s+risks\s*$", re.IGNORECASE)
_VIEW_BETA_RX = re.compile(r"^\s*show\s+beta\s+operations\s*$", re.IGNORECASE)
_VIEW_CUSTOMER_RX = re.compile(r"^\s*show\s+customer\s+operations\s*$", re.IGNORECASE)
_VIEW_DASHBOARD_RX = re.compile(r"^\s*show\s+launch\s+dashboard\s*$", re.IGNORECASE)

_NOTE_RX = re.compile(r"^\s*launch\s+operations\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*launch\s+operations\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_launch_operations_center_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_STATUS_RX.match(text):
        return {"action": "view", "focus": "launch_status_registry"}
    if _VIEW_BLOCKERS_RX.match(text):
        return {"action": "view", "focus": "launch_blocker_registry"}
    if _VIEW_RISKS_RX.match(text):
        return {"action": "view", "focus": "launch_risk_dashboard"}
    if _VIEW_BETA_RX.match(text):
        return {"action": "view", "focus": "beta_operations_monitor"}
    if _VIEW_CUSTOMER_RX.match(text):
        return {"action": "view", "focus": "customer_operations_monitor"}
    if _VIEW_DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "launch_operations_dashboard"}
    if _VIEW_OPS_RX.match(text):
        return {"action": "view", "focus": "launch_operations_dashboard"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"launch_operations_review_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "launch_operations_note",
            "content": note_match.group(1).strip(),
        }

    lowered = text.lower()
    if lowered.startswith("launch operations:") or lowered.startswith("launch ops:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "launch_operations_center_record",
            "content": body,
        }

    return None


def handle_launch_operations_center_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "launch_operations_dashboard"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in LAUNCH_OPERATIONS_CENTER_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_launch_operations_center_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
