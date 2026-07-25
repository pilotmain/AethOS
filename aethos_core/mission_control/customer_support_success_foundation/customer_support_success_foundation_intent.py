# SPDX-License-Identifier: Apache-2.0
"""FIX 310 — customer support & success foundation intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_contract import (
    CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_RECORD_KINDS,
)
from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_store import (
    append_customer_support_success_foundation_record,
)

_VIEW_SUPPORT_RX = re.compile(r"^\s*show\s+customer\s+support\s*$", re.IGNORECASE)
_VIEW_SUCCESS_RX = re.compile(r"^\s*show\s+customer\s+success\s*$", re.IGNORECASE)
_VIEW_HEALTH_RX = re.compile(r"^\s*show\s+customer\s+health\s*$", re.IGNORECASE)
_VIEW_ADOPTION_RX = re.compile(r"^\s*show\s+customer\s+adoption\s*$", re.IGNORECASE)
_VIEW_ESCALATIONS_RX = re.compile(r"^\s*show\s+customer\s+escalations\s*$", re.IGNORECASE)
_VIEW_ANALYTICS_RX = re.compile(r"^\s*show\s+support\s+analytics\s*$", re.IGNORECASE)

_SUPPORT_NOTE_RX = re.compile(r"^\s*support\s+note\s*:\s*(.+)$", re.IGNORECASE)
_SUCCESS_NOTE_RX = re.compile(r"^\s*customer\s+success\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*support\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_customer_support_success_foundation_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_HEALTH_RX.match(text):
        return {"action": "view", "focus": "customer_health_registry"}
    if _VIEW_SUCCESS_RX.match(text):
        return {"action": "view", "focus": "customer_success_dashboard"}
    if _VIEW_ADOPTION_RX.match(text):
        return {"action": "view", "focus": "customer_adoption_report"}
    if _VIEW_ESCALATIONS_RX.match(text):
        return {"action": "view", "focus": "customer_escalation_registry"}
    if _VIEW_ANALYTICS_RX.match(text):
        return {"action": "view", "focus": "support_analytics_dashboard"}
    if _VIEW_SUPPORT_RX.match(text):
        return {"action": "view", "focus": "customer_support_success_dashboard"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"support_review_decision_{decision}",
            "content": body,
        }

    support_note_match = _SUPPORT_NOTE_RX.match(text)
    if support_note_match:
        return {
            "action": "record",
            "kind": "support_note",
            "content": support_note_match.group(1).strip(),
        }

    success_note_match = _SUCCESS_NOTE_RX.match(text)
    if success_note_match:
        return {
            "action": "record",
            "kind": "customer_success_note",
            "content": success_note_match.group(1).strip(),
        }

    lowered = text.lower()
    if lowered.startswith("customer support:") or lowered.startswith("support:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "customer_support_success_foundation_record",
            "content": body,
        }

    return None


def handle_customer_support_success_foundation_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "customer_support_success_dashboard"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_customer_support_success_foundation_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
            org_id=str(intent.get("org_id") or "") or None,
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
