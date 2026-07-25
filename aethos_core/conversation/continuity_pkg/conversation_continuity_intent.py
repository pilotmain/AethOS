# SPDX-License-Identifier: Apache-2.0
"""FIX 316D — continuity review intent parsing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.conversation.continuity_pkg.conversation_continuity_store import append_continuity_review_record

_VIEW_DASHBOARD_RX = re.compile(r"^\s*show\s+continuity\s+dashboard\s*$", re.IGNORECASE)
_VIEW_CONTINUITY_RX = re.compile(r"^\s*show\s+conversation\s+continuity\s*$", re.IGNORECASE)
_NOTE_RX = re.compile(r"^\s*continuity\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*continuity\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_conversation_continuity_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_DASHBOARD_RX.match(text) or _VIEW_CONTINUITY_RX.match(text):
        return {"action": "view", "focus": "continuity_dashboard"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"continuity_review_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "continuity_note",
            "content": note_match.group(1).strip(),
        }

    return None


def handle_conversation_continuity_intent(
    intent: dict[str, Any],
    *,
    session_id: str = "default",
) -> dict[str, Any] | None:
    if intent.get("action") == "record":
        record = append_continuity_review_record(
            kind=str(intent["kind"]),
            content=str(intent["content"]),
            session_id=session_id,
        )
        return {"recorded": record}
    return None
