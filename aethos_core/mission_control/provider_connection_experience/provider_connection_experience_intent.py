# SPDX-License-Identifier: Apache-2.0
"""FIX 303 — provider connection experience intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_contract import (
    PROVIDER_CONNECTION_EXPERIENCE_RECORD_KINDS,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_store import (
    append_provider_connection_experience_record,
)

_VIEW_CONNECTIONS_RX = re.compile(
    r"^\s*show\s+provider\s+connections\s*$",
    re.IGNORECASE,
)
_VIEW_READINESS_RX = re.compile(r"^\s*show\s+provider\s+readiness\s*$", re.IGNORECASE)
_VIEW_UNLOCKS_RX = re.compile(r"^\s*show\s+provider\s+capability\s+unlocks\s*$", re.IGNORECASE)

_NOTE_RX = re.compile(r"^\s*provider\s+connection\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*provider\s+connection\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_provider_connection_experience_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_READINESS_RX.match(text):
        return {"action": "view", "focus": "provider_connection_readiness_report"}
    if _VIEW_UNLOCKS_RX.match(text):
        return {"action": "view", "focus": "provider_capability_unlock_matrix"}
    if _VIEW_CONNECTIONS_RX.match(text):
        return {"action": "view", "focus": "provider_connection_dashboard"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"provider_connection_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "provider_connection_note",
            "content": note_match.group(1).strip(),
        }

    lowered = text.lower()
    if lowered.startswith("provider connection:") or lowered.startswith("provider:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "provider_connection_experience_record",
            "content": body,
        }

    return None


def handle_provider_connection_experience_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "provider_connection_dashboard"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in PROVIDER_CONNECTION_EXPERIENCE_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_provider_connection_experience_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=session_id,
            provider=str(intent.get("provider") or "") or None,
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
