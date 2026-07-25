# SPDX-License-Identifier: Apache-2.0
"""PHASE_I1 / FIX 361 — operator intent parsing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_contract import (
    AUTONOMOUS_EXECUTION_RECORD_KINDS,
)
from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_executor import (
    register_autonomous_execution_request_from_text,
)
from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_store import (
    append_autonomous_execution_record,
)

_DASHBOARD_RX = re.compile(r"^\s*show\s+autonomous\s+execution\s+dashboard\s*$", re.IGNORECASE)
_REQUEST_RX = re.compile(r"^\s*autonomous\s+execution\s+request\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)
_NOTE_RX = re.compile(r"^\s*autonomous\s+execution\s+note\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)
_REVIEW_RX = re.compile(
    r"^\s*autonomous\s+execution\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_autonomous_execution_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "autonomous_execution_dashboard"}

    request_match = _REQUEST_RX.match(text)
    if request_match:
        body = (request_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "request", "body": body}

    note_match = _NOTE_RX.match(text)
    if note_match:
        body = (note_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "record", "kind": "autonomous_execution_note", "content": body}

    review_match = _REVIEW_RX.match(text)
    if review_match:
        decision = review_match.group("decision").lower()
        body = (review_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"autonomous_execution_review_{decision}",
            "content": body,
        }

    lowered = text.lower()
    if lowered.startswith("phase i1:") or lowered.startswith("autonomous execution:"):
        body = text.split(":", 1)[1].strip()
        return {"action": "record", "kind": "autonomous_execution_record", "content": body}

    return None


def handle_autonomous_execution_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    sid = (session_id or "default").strip()[:64] or "default"

    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "autonomous_execution_dashboard"}

    if action == "request":
        entry = register_autonomous_execution_request_from_text(
            program_session_id=sid,
            body=str(intent.get("body") or ""),
        )
        return {"action": "request", "entry": entry}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in AUTONOMOUS_EXECUTION_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_autonomous_execution_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=sid,
            metadata=dict(intent.get("metadata") or {}),
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
