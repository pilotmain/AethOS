# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F4 / FIX 350 — operator intent parsing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_contract import (
    CUSTOMER_SCALE_VALIDATION_RECORD_KINDS,
)
from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_executor import (
    register_scale_cohort_customer_from_text,
)
from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_store import (
    append_customer_scale_validation_record,
)

_DASHBOARD_RX = re.compile(r"^\s*show\s+customer\s+scale\s+dashboard\s*$", re.IGNORECASE)
_COHORT_RX = re.compile(r"^\s*customer\s+scale\s+cohort\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)
_NOTE_RX = re.compile(r"^\s*customer\s+scale\s+note\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)
_REVIEW_RX = re.compile(
    r"^\s*customer\s+scale\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_customer_scale_validation_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "customer_scale_dashboard"}

    cohort_match = _COHORT_RX.match(text)
    if cohort_match:
        body = (cohort_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "cohort", "body": body}

    note_match = _NOTE_RX.match(text)
    if note_match:
        body = (note_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "record", "kind": "customer_scale_note", "content": body}

    review_match = _REVIEW_RX.match(text)
    if review_match:
        decision = review_match.group("decision").lower()
        body = (review_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"customer_scale_review_{decision}",
            "content": body,
        }

    lowered = text.lower()
    if lowered.startswith("workstream f4:") or lowered.startswith("customer scale validation:"):
        body = text.split(":", 1)[1].strip()
        return {"action": "record", "kind": "customer_scale_validation_record", "content": body}

    return None


def handle_customer_scale_validation_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    sid = (session_id or "default").strip()[:64] or "default"

    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "customer_scale_dashboard"}

    if action == "cohort":
        entry = register_scale_cohort_customer_from_text(program_session_id=sid, body=str(intent.get("body") or ""))
        return {"action": "cohort", "entry": entry}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in CUSTOMER_SCALE_VALIDATION_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_customer_scale_validation_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=sid,
            metadata=dict(intent.get("metadata") or {}),
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
