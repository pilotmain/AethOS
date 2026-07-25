# SPDX-License-Identifier: Apache-2.0
"""FIX 316C — truth review intent parsing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.truth_consistency.truth_consistency_store import append_truth_review_record

_VIEW_DASHBOARD_RX = re.compile(r"^\s*show\s+truth\s+dashboard\s*$", re.IGNORECASE)
_VIEW_CONSISTENCY_RX = re.compile(r"^\s*show\s+truth\s+consistency\s*$", re.IGNORECASE)
_NOTE_RX = re.compile(r"^\s*truth\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*truth\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_truth_consistency_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_DASHBOARD_RX.match(text) or _VIEW_CONSISTENCY_RX.match(text):
        return {"action": "view", "focus": "truth_dashboard"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"truth_review_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "truth_note",
            "content": note_match.group(1).strip(),
        }

    return None


def handle_truth_consistency_intent(
    intent: dict[str, Any],
    *,
    session_id: str = "default",
) -> dict[str, Any] | None:
    if intent.get("action") == "record":
        record = append_truth_review_record(
            kind=str(intent["kind"]),
            content=str(intent["content"]),
            session_id=session_id,
        )
        return {"recorded": record}
    return None
