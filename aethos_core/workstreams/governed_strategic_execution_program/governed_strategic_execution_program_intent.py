# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_H2 / FIX 359 — operator intent parsing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_contract import (
    STRATEGIC_EXECUTION_RECORD_KINDS,
)
from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_executor import (
    register_strategic_initiative_from_text,
)
from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_store import (
    append_strategic_execution_record,
)

_DASHBOARD_RX = re.compile(r"^\s*show\s+strategic\s+execution\s+dashboard\s*$", re.IGNORECASE)
_INITIATIVE_RX = re.compile(r"^\s*strategic\s+execution\s+initiative\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)
_NOTE_RX = re.compile(r"^\s*strategic\s+execution\s+note\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)
_REVIEW_RX = re.compile(
    r"^\s*strategic\s+execution\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_strategic_execution_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "strategic_execution_dashboard"}

    initiative_match = _INITIATIVE_RX.match(text)
    if initiative_match:
        body = (initiative_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "initiative", "body": body}

    note_match = _NOTE_RX.match(text)
    if note_match:
        body = (note_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "record", "kind": "strategic_execution_note", "content": body}

    review_match = _REVIEW_RX.match(text)
    if review_match:
        decision = review_match.group("decision").lower()
        body = (review_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"strategic_execution_review_{decision}",
            "content": body,
        }

    lowered = text.lower()
    if lowered.startswith("workstream h2:") or lowered.startswith("strategic execution:"):
        body = text.split(":", 1)[1].strip()
        return {"action": "record", "kind": "strategic_execution_record", "content": body}

    return None


def handle_strategic_execution_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    sid = (session_id or "default").strip()[:64] or "default"

    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "strategic_execution_dashboard"}

    if action == "initiative":
        entry = register_strategic_initiative_from_text(
            program_session_id=sid,
            body=str(intent.get("body") or ""),
        )
        return {"action": "initiative", "entry": entry}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in STRATEGIC_EXECUTION_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_strategic_execution_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=sid,
            metadata=dict(intent.get("metadata") or {}),
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
