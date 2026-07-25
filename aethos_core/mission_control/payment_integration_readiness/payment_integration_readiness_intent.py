# SPDX-License-Identifier: Apache-2.0
"""FIX 308 — payment integration readiness intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_contract import (
    PAYMENT_INTEGRATION_READINESS_RECORD_KINDS,
)
from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_store import (
    append_payment_integration_readiness_record,
)

_VIEW_READINESS_RX = re.compile(r"^\s*show\s+payment\s+readiness\s*$", re.IGNORECASE)
_VIEW_EVENTS_RX = re.compile(r"^\s*show\s+billing\s+events\s*$", re.IGNORECASE)
_VIEW_ANALYTICS_RX = re.compile(r"^\s*show\s+commercial\s+analytics\s*$", re.IGNORECASE)
_VIEW_UPGRADES_RX = re.compile(r"^\s*show\s+upgrade\s+paths\s*$", re.IGNORECASE)

_NOTE_RX = re.compile(r"^\s*payment\s+readiness\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*payment\s+readiness\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_payment_integration_readiness_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_EVENTS_RX.match(text):
        return {"action": "view", "focus": "billing_event_registry"}
    if _VIEW_ANALYTICS_RX.match(text):
        return {"action": "view", "focus": "commercial_analytics_dashboard"}
    if _VIEW_UPGRADES_RX.match(text):
        return {"action": "view", "focus": "upgrade_path_registry"}
    if _VIEW_READINESS_RX.match(text):
        return {"action": "view", "focus": "payment_readiness_dashboard"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"payment_readiness_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "payment_readiness_note",
            "content": note_match.group(1).strip(),
        }

    lowered = text.lower()
    if lowered.startswith("payment readiness:") or lowered.startswith("payment:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "payment_integration_readiness_record",
            "content": body,
        }

    return None


def handle_payment_integration_readiness_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "payment_readiness_dashboard"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in PAYMENT_INTEGRATION_READINESS_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_payment_integration_readiness_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=session_id,
            provider=str(intent.get("provider") or "") or None,
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
