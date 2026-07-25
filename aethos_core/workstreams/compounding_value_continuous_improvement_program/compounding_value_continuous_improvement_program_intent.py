# SPDX-License-Identifier: Apache-2.0
"""PHASE_J3 / FIX 366 — operator intent parsing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.compounding_value_continuous_improvement_program.compounding_value_continuous_improvement_program_contract import (
    CONTINUOUS_IMPROVEMENT_RECORD_KINDS,
)
from aethos_core.workstreams.compounding_value_continuous_improvement_program.compounding_value_continuous_improvement_program_executor import (
    register_improvement_baseline_from_text,
)
from aethos_core.workstreams.compounding_value_continuous_improvement_program.compounding_value_continuous_improvement_program_store import (
    append_continuous_improvement_record,
)

_DASHBOARD_RX = re.compile(r"^\s*show\s+compounding\s+value\s+dashboard\s*$", re.IGNORECASE)
_BASELINE_RX = re.compile(
    r"^\s*continuous\s+improvement\s+baseline\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_NOTE_RX = re.compile(r"^\s*continuous\s+improvement\s+note\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)
_REVIEW_RX = re.compile(
    r"^\s*continuous\s+improvement\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_continuous_improvement_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "compounding_value_dashboard"}

    baseline_match = _BASELINE_RX.match(text)
    if baseline_match:
        body = (baseline_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "baseline", "body": body}

    note_match = _NOTE_RX.match(text)
    if note_match:
        body = (note_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "record", "kind": "continuous_improvement_note", "content": body}

    review_match = _REVIEW_RX.match(text)
    if review_match:
        decision = review_match.group("decision").lower()
        body = (review_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"continuous_improvement_review_{decision}",
            "content": body,
        }

    lowered = text.lower()
    if lowered.startswith("phase j3:") or lowered.startswith("continuous improvement:"):
        body = text.split(":", 1)[1].strip()
        return {"action": "record", "kind": "continuous_improvement_record", "content": body}

    return None


def handle_continuous_improvement_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    sid = (session_id or "default").strip()[:64] or "default"

    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "compounding_value_dashboard"}

    if action == "baseline":
        entry = register_improvement_baseline_from_text(
            program_session_id=sid,
            body=str(intent.get("body") or ""),
        )
        return {"action": "baseline", "entry": entry}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in CONTINUOUS_IMPROVEMENT_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_continuous_improvement_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=sid,
            metadata=dict(intent.get("metadata") or {}),
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
