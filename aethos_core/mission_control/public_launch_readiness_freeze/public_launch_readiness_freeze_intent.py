# SPDX-License-Identifier: Apache-2.0
"""FIX 314 — public launch readiness freeze intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_contract import (
    PUBLIC_LAUNCH_READINESS_FREEZE_RECORD_KINDS,
)
from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_store import (
    append_public_launch_readiness_freeze_record,
)

_VIEW_FREEZE_RX = re.compile(r"^\s*show\s+launch\s+readiness\s+freeze\s*$", re.IGNORECASE)
_VIEW_BASELINE_RX = re.compile(r"^\s*show\s+launch\s+baseline\s*$", re.IGNORECASE)
_VIEW_EVIDENCE_RX = re.compile(r"^\s*show\s+launch\s+evidence\s+freeze\s*$", re.IGNORECASE)
_VIEW_RECOMMENDATION_RX = re.compile(r"^\s*show\s+launch\s+recommendation\s+freeze\s*$", re.IGNORECASE)

_NOTE_RX = re.compile(r"^\s*launch\s+freeze\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*launch\s+freeze\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_public_launch_readiness_freeze_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_EVIDENCE_RX.match(text):
        return {"action": "view", "focus": "launch_evidence_timeline"}
    if _VIEW_RECOMMENDATION_RX.match(text):
        return {"action": "view", "focus": "launch_recommendation_freeze"}
    if _VIEW_BASELINE_RX.match(text):
        return {"action": "view", "focus": "launch_readiness_freeze_dashboard"}
    if _VIEW_FREEZE_RX.match(text):
        return {"action": "view", "focus": "launch_readiness_freeze_dashboard"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"launch_freeze_review_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "launch_freeze_note",
            "content": note_match.group(1).strip(),
        }

    lowered = text.lower()
    if lowered.startswith("launch freeze:") or lowered.startswith("launch baseline:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "public_launch_readiness_freeze_record",
            "content": body,
        }

    return None


def handle_public_launch_readiness_freeze_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "launch_readiness_freeze_dashboard"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in PUBLIC_LAUNCH_READINESS_FREEZE_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_public_launch_readiness_freeze_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
