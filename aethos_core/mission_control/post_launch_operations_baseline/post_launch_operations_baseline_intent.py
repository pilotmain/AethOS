# SPDX-License-Identifier: Apache-2.0
"""FIX 316 — post-launch operations baseline intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_contract import (
    POST_LAUNCH_OPERATIONS_BASELINE_RECORD_KINDS,
)
from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_store import (
    append_post_launch_operations_baseline_record,
)

_VIEW_BASELINE_RX = re.compile(r"^\s*show\s+post\s+launch\s+operations\s+baseline\s*$", re.IGNORECASE)
_VIEW_PLATFORM_RX = re.compile(r"^\s*show\s+platform\s+baseline\s*$", re.IGNORECASE)
_VIEW_CUSTOMER_RX = re.compile(r"^\s*show\s+customer\s+baseline\s*$", re.IGNORECASE)
_VIEW_GOVERNANCE_RX = re.compile(r"^\s*show\s+governance\s+baseline\s*$", re.IGNORECASE)
_VIEW_INCIDENT_RX = re.compile(r"^\s*show\s+incident\s+baseline\s*$", re.IGNORECASE)
_VIEW_DASHBOARD_RX = re.compile(r"^\s*show\s+operations\s+dashboard\s*$", re.IGNORECASE)

_NOTE_RX = re.compile(r"^\s*operations\s+baseline\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*operations\s+baseline\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_post_launch_operations_baseline_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_PLATFORM_RX.match(text):
        return {"action": "view", "focus": "platform_health_baseline"}
    if _VIEW_CUSTOMER_RX.match(text):
        return {"action": "view", "focus": "customer_health_baseline"}
    if _VIEW_GOVERNANCE_RX.match(text):
        return {"action": "view", "focus": "governance_health_baseline"}
    if _VIEW_INCIDENT_RX.match(text):
        return {"action": "view", "focus": "incident_baseline"}
    if _VIEW_DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "post_launch_operations_dashboard"}
    if _VIEW_BASELINE_RX.match(text):
        return {"action": "view", "focus": "post_launch_operations_dashboard"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"operations_baseline_review_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "operations_baseline_note",
            "content": note_match.group(1).strip(),
        }

    lowered = text.lower()
    if lowered.startswith("operations baseline:") or lowered.startswith("post launch baseline:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "operations_baseline_record",
            "content": body,
        }

    return None


def handle_post_launch_operations_baseline_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "post_launch_operations_dashboard"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in POST_LAUNCH_OPERATIONS_BASELINE_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_post_launch_operations_baseline_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
