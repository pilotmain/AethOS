# SPDX-License-Identifier: Apache-2.0
"""FIX 304 — channel integration foundation intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_contract import (
    CHANNEL_INTEGRATION_FOUNDATION_RECORD_KINDS,
)
from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_store import (
    append_channel_integration_foundation_record,
)

_VIEW_CHANNELS_RX = re.compile(r"^\s*show\s+channels\s*$", re.IGNORECASE)
_VIEW_READINESS_RX = re.compile(r"^\s*show\s+channel\s+readiness\s*$", re.IGNORECASE)
_VIEW_AUTH_RX = re.compile(r"^\s*show\s+channel\s+authorization\s*$", re.IGNORECASE)
_VIEW_CAPS_RX = re.compile(r"^\s*show\s+channel\s+capabilities\s*$", re.IGNORECASE)

_NOTE_RX = re.compile(r"^\s*channel\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*channel\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_channel_integration_foundation_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_READINESS_RX.match(text):
        return {"action": "view", "focus": "channel_readiness"}
    if _VIEW_AUTH_RX.match(text):
        return {"action": "view", "focus": "channel_authorization_report"}
    if _VIEW_CAPS_RX.match(text):
        return {"action": "view", "focus": "channel_capability_matrix"}
    if _VIEW_CHANNELS_RX.match(text):
        return {"action": "view", "focus": "channel_dashboard"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"channel_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "channel_note",
            "content": note_match.group(1).strip(),
        }

    lowered = text.lower()
    if lowered.startswith("channel:") or lowered.startswith("channels:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "channel_integration_foundation_record",
            "content": body,
        }

    return None


def handle_channel_integration_foundation_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "channel_dashboard"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in CHANNEL_INTEGRATION_FOUNDATION_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_channel_integration_foundation_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=session_id,
            channel=str(intent.get("channel") or "") or None,
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
