# SPDX-License-Identifier: Apache-2.0
"""FIX 307 — customer usage & audit portal intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_contract import (
    CUSTOMER_USAGE_AUDIT_PORTAL_RECORD_KINDS,
)
from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_store import (
    append_customer_usage_audit_portal_record,
)

_VIEW_PORTAL_RX = re.compile(r"^\s*show\s+audit\s+portal\s*$", re.IGNORECASE)
_VIEW_ACTIVITY_RX = re.compile(r"^\s*show\s+activity\s+timeline\s*$", re.IGNORECASE)
_VIEW_GOV_RX = re.compile(r"^\s*show\s+governance\s+timeline\s*$", re.IGNORECASE)
_VIEW_USAGE_RX = re.compile(r"^\s*show\s+usage\s+timeline\s*$", re.IGNORECASE)
_VIEW_EVIDENCE_RX = re.compile(r"^\s*show\s+evidence\s+explorer\s*$", re.IGNORECASE)

_NOTE_RX = re.compile(r"^\s*audit\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*audit\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_customer_usage_audit_portal_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_ACTIVITY_RX.match(text):
        return {"action": "view", "focus": "activity_timeline"}
    if _VIEW_GOV_RX.match(text):
        return {"action": "view", "focus": "governance_timeline"}
    if _VIEW_USAGE_RX.match(text):
        return {"action": "view", "focus": "usage_timeline"}
    if _VIEW_EVIDENCE_RX.match(text):
        return {"action": "view", "focus": "evidence_explorer"}
    if _VIEW_PORTAL_RX.match(text):
        return {"action": "view", "focus": "customer_audit_dashboard"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"audit_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "audit_note",
            "content": note_match.group(1).strip(),
        }

    lowered = text.lower()
    if lowered.startswith("audit:") or lowered.startswith("audit portal:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "customer_usage_audit_portal_record",
            "content": body,
        }

    return None


def handle_customer_usage_audit_portal_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "customer_audit_dashboard"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in CUSTOMER_USAGE_AUDIT_PORTAL_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_customer_usage_audit_portal_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
