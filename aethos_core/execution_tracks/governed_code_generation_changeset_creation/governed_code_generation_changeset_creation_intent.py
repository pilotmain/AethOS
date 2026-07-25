# SPDX-License-Identifier: Apache-2.0
"""FIX 335 / EXECUTION_TRACK_2 — operator intent parsing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_contract import (
    GOVERNED_CODE_GENERATION_RECORD_KINDS,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_executor import (
    execute_code_generation,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_store import (
    append_governed_code_generation_record,
)

_DASHBOARD_RX = re.compile(r"^\s*show\s+code\s+generation\s+dashboard\s*$", re.IGNORECASE)
_CHANGESET_RX = re.compile(r"^\s*show\s+changeset\s+review\s+package\s*$", re.IGNORECASE)

_REQUEST_REVIEW_RX = re.compile(
    r"^\s*generation\s+request\s+review\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_GENERATE_REVIEW_RX = re.compile(
    r"^\s*generate\s+code\s+review\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_DECISION_RX = re.compile(
    r"^\s*generation\s+decision\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)

_KV_RX = re.compile(r"(\w+)\s*=\s*([^,\s]+)")


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in _KV_RX.finditer(blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def parse_governed_code_generation_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "code_generation_dashboard"}
    if _CHANGESET_RX.match(text):
        return {"action": "view", "focus": "changeset_review_package"}

    request_match = _REQUEST_REVIEW_RX.match(text)
    if request_match:
        body = (request_match.group("body") or "").strip()
        kv = _parse_kv_blob(body)
        return {
            "action": "record",
            "kind": "generation_request_review_note",
            "content": body,
            "metadata": {
                "type": kv.get("type") or kv.get("requirement_type") or "task",
                "requirement_type": kv.get("type") or kv.get("requirement_type") or "task",
                "feature_name": kv.get("feature") or kv.get("feature_name") or kv.get("title"),
                "title": kv.get("title") or kv.get("feature") or kv.get("feature_name"),
                "stack": kv.get("stack"),
            },
        }

    generate_match = _GENERATE_REVIEW_RX.match(text)
    if generate_match:
        body = (generate_match.group("body") or "").strip()
        kv = _parse_kv_blob(body)
        return {
            "action": "record",
            "kind": "generate_code_review_note",
            "content": body,
            "metadata": {
                "stack": kv.get("stack"),
                "feature_name": kv.get("feature") or kv.get("feature_name"),
            },
        }

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"generation_decision_{decision}",
            "content": body,
        }

    lowered = text.lower()
    if lowered.startswith("execution track 2:") or lowered.startswith("code generation:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "governed_code_generation_record",
            "content": body,
        }

    return None


def handle_governed_code_generation_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    sid = (session_id or "default").strip()[:64] or "default"

    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "code_generation_dashboard"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in GOVERNED_CODE_GENERATION_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_governed_code_generation_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=sid,
            metadata=dict(intent.get("metadata") or {}),
        )
        result: dict[str, Any] = {"action": "record", "record": record}
        if kind == "generation_decision_approve":
            generation = execute_code_generation(session_id=sid)
            result["generation"] = generation
        return result

    raise ValueError(f"unsupported intent action: {action!r}")
