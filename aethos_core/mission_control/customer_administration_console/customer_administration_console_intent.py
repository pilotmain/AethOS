# SPDX-License-Identifier: Apache-2.0
"""FIX 306 — customer administration console intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.customer_administration_console.customer_administration_console_contract import (
    CUSTOMER_ADMINISTRATION_CONSOLE_RECORD_KINDS,
)
from aethos_core.mission_control.customer_administration_console.customer_administration_console_store import (
    append_customer_administration_console_record,
)

_VIEW_CONSOLE_RX = re.compile(r"^\s*show\s+administration\s+console\s*$", re.IGNORECASE)
_VIEW_ORG_RX = re.compile(r"^\s*show\s+organization\s+administration\s*$", re.IGNORECASE)
_VIEW_USER_RX = re.compile(r"^\s*show\s+user\s+administration\s*$", re.IGNORECASE)
_VIEW_PROVIDER_RX = re.compile(r"^\s*show\s+provider\s+administration\s*$", re.IGNORECASE)
_VIEW_GOV_RX = re.compile(r"^\s*show\s+governance\s+administration\s*$", re.IGNORECASE)

_NOTE_RX = re.compile(r"^\s*administration\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*administration\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_customer_administration_console_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_ORG_RX.match(text):
        return {"action": "view", "focus": "organization_administration_report"}
    if _VIEW_USER_RX.match(text):
        return {"action": "view", "focus": "user_administration_report"}
    if _VIEW_PROVIDER_RX.match(text):
        return {"action": "view", "focus": "provider_administration_report"}
    if _VIEW_GOV_RX.match(text):
        return {"action": "view", "focus": "governance_administration_report"}
    if _VIEW_CONSOLE_RX.match(text):
        return {"action": "view", "focus": "customer_administration_dashboard"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"administration_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "administration_note",
            "content": note_match.group(1).strip(),
        }

    lowered = text.lower()
    if lowered.startswith("administration:") or lowered.startswith("admin console:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "customer_administration_console_record",
            "content": body,
        }

    return None


def handle_customer_administration_console_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "customer_administration_dashboard"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in CUSTOMER_ADMINISTRATION_CONSOLE_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_customer_administration_console_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
