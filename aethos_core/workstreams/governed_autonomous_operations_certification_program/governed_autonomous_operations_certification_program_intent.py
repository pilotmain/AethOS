# SPDX-License-Identifier: Apache-2.0
"""PHASE_I3 / FIX 363 — operator intent parsing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_contract import (
    AUTONOMOUS_CERTIFICATION_RECORD_KINDS,
)
from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_executor import (
    register_certification_candidate_from_text,
)
from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_store import (
    append_autonomous_certification_record,
)

_DASHBOARD_RX = re.compile(
    r"^\s*show\s+autonomous\s+operations\s+certification\s+dashboard\s*$",
    re.IGNORECASE,
)
_CANDIDATE_RX = re.compile(
    r"^\s*autonomous\s+certification\s+candidate\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_NOTE_RX = re.compile(r"^\s*autonomous\s+certification\s+note\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)
_REVIEW_RX = re.compile(
    r"^\s*autonomous\s+certification\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_autonomous_certification_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "autonomous_operations_certification_dashboard"}

    candidate_match = _CANDIDATE_RX.match(text)
    if candidate_match:
        body = (candidate_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "candidate", "body": body}

    note_match = _NOTE_RX.match(text)
    if note_match:
        body = (note_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "record", "kind": "autonomous_certification_note", "content": body}

    review_match = _REVIEW_RX.match(text)
    if review_match:
        decision = review_match.group("decision").lower()
        body = (review_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"autonomous_certification_review_{decision}",
            "content": body,
        }

    lowered = text.lower()
    if lowered.startswith("phase i3:") or lowered.startswith("autonomous certification:"):
        body = text.split(":", 1)[1].strip()
        return {"action": "record", "kind": "autonomous_certification_record", "content": body}

    return None


def handle_autonomous_certification_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    sid = (session_id or "default").strip()[:64] or "default"

    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "autonomous_operations_certification_dashboard"}

    if action == "candidate":
        entry = register_certification_candidate_from_text(
            program_session_id=sid,
            body=str(intent.get("body") or ""),
        )
        return {"action": "candidate", "entry": entry}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in AUTONOMOUS_CERTIFICATION_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_autonomous_certification_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=sid,
            metadata=dict(intent.get("metadata") or {}),
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
