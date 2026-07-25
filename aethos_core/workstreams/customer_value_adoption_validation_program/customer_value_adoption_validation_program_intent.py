# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F2 / FIX 348 — operator intent parsing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_contract import (
    CUSTOMER_VALUE_ADOPTION_VALIDATION_RECORD_KINDS,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_executor import (
    record_customer_usage_observation,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_store import (
    append_customer_value_adoption_validation_record,
)

_DASHBOARD_RX = re.compile(r"^\s*show\s+customer\s+value\s+dashboard\s*$", re.IGNORECASE)
_USAGE_RX = re.compile(
    r"^\s*customer\s+usage\s+observation\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_NOTE_RX = re.compile(r"^\s*customer\s+value\s+note\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)
_REVIEW_RX = re.compile(
    r"^\s*customer\s+value\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_customer_value_adoption_validation_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "customer_value_dashboard"}

    usage_match = _USAGE_RX.match(text)
    if usage_match:
        body = (usage_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "observe", "body": body}

    note_match = _NOTE_RX.match(text)
    if note_match:
        body = (note_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "record", "kind": "customer_value_note", "content": body}

    review_match = _REVIEW_RX.match(text)
    if review_match:
        decision = review_match.group("decision").lower()
        body = (review_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"customer_value_review_{decision}",
            "content": body,
        }

    lowered = text.lower()
    if lowered.startswith("workstream f2:") or lowered.startswith("customer value adoption:"):
        body = text.split(":", 1)[1].strip()
        return {"action": "record", "kind": "customer_value_validation_record", "content": body}

    return None


def handle_customer_value_adoption_validation_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    sid = (session_id or "default").strip()[:64] or "default"

    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "customer_value_dashboard"}

    if action == "observe":
        observation = record_customer_usage_observation(session_id=sid, body=str(intent.get("body") or ""))
        return {"action": "observe", "observation": observation}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in CUSTOMER_VALUE_ADOPTION_VALIDATION_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_customer_value_adoption_validation_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=sid,
            metadata=dict(intent.get("metadata") or {}),
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
