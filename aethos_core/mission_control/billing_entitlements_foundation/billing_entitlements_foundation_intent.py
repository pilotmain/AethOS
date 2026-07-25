# SPDX-License-Identifier: Apache-2.0
"""FIX 305 — billing & entitlements foundation intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_contract import (
    BILLING_ENTITLEMENTS_FOUNDATION_RECORD_KINDS,
)
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_store import (
    append_billing_entitlements_foundation_record,
)

_VIEW_BILLING_RX = re.compile(r"^\s*show\s+billing\s*$", re.IGNORECASE)
_VIEW_ENTITLEMENTS_RX = re.compile(r"^\s*show\s+entitlements\s*$", re.IGNORECASE)
_VIEW_USAGE_LIMITS_RX = re.compile(r"^\s*show\s+usage\s+limits\s*$", re.IGNORECASE)
_VIEW_SUBSCRIPTION_RX = re.compile(r"^\s*show\s+subscription\s+status\s*$", re.IGNORECASE)

_NOTE_RX = re.compile(r"^\s*billing\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*billing\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_billing_entitlements_foundation_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_ENTITLEMENTS_RX.match(text):
        return {"action": "view", "focus": "entitlement_registry"}
    if _VIEW_USAGE_LIMITS_RX.match(text):
        return {"action": "view", "focus": "usage_limit_report"}
    if _VIEW_SUBSCRIPTION_RX.match(text):
        return {"action": "view", "focus": "subscription_registry"}
    if _VIEW_BILLING_RX.match(text):
        return {"action": "view", "focus": "billing_dashboard"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"billing_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "billing_note",
            "content": note_match.group(1).strip(),
        }

    lowered = text.lower()
    if lowered.startswith("billing:") or lowered.startswith("entitlements:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "billing_entitlements_foundation_record",
            "content": body,
        }

    return None


def handle_billing_entitlements_foundation_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "billing_dashboard"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in BILLING_ENTITLEMENTS_FOUNDATION_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_billing_entitlements_foundation_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=session_id,
            plan=str(intent.get("plan") or "") or None,
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
