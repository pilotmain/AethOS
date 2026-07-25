# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F1 / FIX 347 — operator intent parsing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_contract import (
    FIRST_CUSTOMER_DELIVERY_PILOT_RECORD_KINDS,
    RECOMMENDED_PILOT_REQUEST_TYPES,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_executor import (
    intake_customer_delivery_request_from_text,
    run_customer_delivery_pilot,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_store import (
    append_first_customer_delivery_pilot_record,
)

_DASHBOARD_RX = re.compile(r"^\s*show\s+customer\s+delivery\s+pilot\s+dashboard\s*$", re.IGNORECASE)
_REQUEST_RX = re.compile(r"^\s*customer\s+delivery\s+request\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)
_RUN_RX = re.compile(r"^\s*customer\s+delivery\s+pilot\s+run(?:\s*:\s*(?P<body>.+))?\s*$", re.IGNORECASE | re.S)
_NOTE_RX = re.compile(r"^\s*customer\s+pilot\s+note\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)
_REVIEW_RX = re.compile(
    r"^\s*customer\s+pilot\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_KV_RX = re.compile(r"(\w+)\s*=\s*([^,\s]+)")


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in _KV_RX.finditer(blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def parse_first_customer_delivery_pilot_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "customer_delivery_pilot_dashboard"}

    request_match = _REQUEST_RX.match(text)
    if request_match:
        body = (request_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "intake", "body": body}

    run_match = _RUN_RX.match(text)
    if run_match:
        body = (run_match.group("body") or "").strip()
        kv = _parse_kv_blob(body) if body else {}
        return {
            "action": "run",
            "request_type": kv.get("type") or kv.get("request_type"),
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        body = (note_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "record", "kind": "customer_pilot_note", "content": body}

    review_match = _REVIEW_RX.match(text)
    if review_match:
        decision = review_match.group("decision").lower()
        body = (review_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"customer_pilot_review_{decision}",
            "content": body,
        }

    lowered = text.lower()
    if lowered.startswith("workstream f1:") or lowered.startswith("customer delivery pilot:"):
        body = text.split(":", 1)[1].strip()
        return {"action": "record", "kind": "first_customer_delivery_pilot_record", "content": body}

    return None


def handle_first_customer_delivery_pilot_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    sid = (session_id or "default").strip()[:64] or "default"

    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "customer_delivery_pilot_dashboard"}

    if action == "intake":
        result = intake_customer_delivery_request_from_text(session_id=sid, body=str(intent.get("body") or ""))
        return {"action": "intake", "result": result}

    if action == "run":
        request_type = intent.get("request_type")
        if request_type and str(request_type).strip().lower().replace("-", "_") not in RECOMMENDED_PILOT_REQUEST_TYPES:
            request_type = None
        result = run_customer_delivery_pilot(session_id=sid, request_type=request_type)
        return {"action": "run", "result": result}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in FIRST_CUSTOMER_DELIVERY_PILOT_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_first_customer_delivery_pilot_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=sid,
            metadata=dict(intent.get("metadata") or {}),
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
