# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_C1 / FIX 339 — operator intent parsing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_contract import (
    CANDIDATE_TYPES,
    REAL_WORLD_DELIVERY_PROOF_RECORD_KINDS,
)
from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_executor import (
    run_delivery_proof,
)
from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_store import (
    append_real_world_delivery_proof_record,
    register_delivery_candidate,
)


_DASHBOARD_RX = re.compile(r"^\s*show\s+delivery\s+proof\s+dashboard\s*$", re.IGNORECASE)
_STATUS_RX = re.compile(r"^\s*show\s+delivery\s+proof\s+status\s*$", re.IGNORECASE)

_NOTE_RX = re.compile(r"^\s*delivery\s+proof\s+note\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)
_REVIEW_RX = re.compile(
    r"^\s*delivery\s+proof\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_RUN_RX = re.compile(r"^\s*delivery\s+proof\s+run\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)
_CANDIDATE_RX = re.compile(r"^\s*delivery\s+proof\s+candidate\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)

_KV_RX = re.compile(r"(\w+)\s*=\s*([^,\s]+)")


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in _KV_RX.finditer(blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def parse_real_world_delivery_proof_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "delivery_proof_dashboard"}
    if _STATUS_RX.match(text):
        return {"action": "view", "focus": "delivery_proof_status"}

    run_match = _RUN_RX.match(text)
    if run_match:
        body = (run_match.group("body") or "").strip()
        kv = _parse_kv_blob(body)
        repository = kv.get("repository") or kv.get("repo") or ""
        if not repository:
            return None
        return {
            "action": "run",
            "repository": repository,
            "candidate_type": kv.get("type") or kv.get("candidate_type"),
            "metadata": kv,
        }

    candidate_match = _CANDIDATE_RX.match(text)
    if candidate_match:
        body = (candidate_match.group("body") or "").strip()
        kv = _parse_kv_blob(body)
        repository = kv.get("repository") or kv.get("repo") or ""
        if not repository:
            return None
        return {
            "action": "candidate",
            "repository": repository,
            "candidate_type": kv.get("type") or kv.get("candidate_type") or "low_risk_enhancement",
            "content": body,
            "metadata": kv,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        body = (note_match.group("body") or "").strip()
        if not body:
            return None
        kv = _parse_kv_blob(body)
        return {
            "action": "record",
            "kind": "delivery_proof_note",
            "content": body,
            "metadata": kv,
        }

    review_match = _REVIEW_RX.match(text)
    if review_match:
        decision = review_match.group("decision").lower()
        body = (review_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"delivery_proof_review_{decision}",
            "content": body,
        }

    lowered = text.lower()
    if lowered.startswith("workstream c1:") or lowered.startswith("delivery proof:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "real_world_delivery_proof_record",
            "content": body,
        }

    return None


def handle_real_world_delivery_proof_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    sid = (session_id or "default").strip()[:64] or "default"

    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "delivery_proof_dashboard"}

    if action == "run":
        result = run_delivery_proof(
            session_id=sid,
            repository=str(intent.get("repository") or ""),
            candidate_type=intent.get("candidate_type"),
        )
        return {"action": "run", "result": result}

    if action == "candidate":
        candidate_type = str(intent.get("candidate_type") or "low_risk_enhancement")
        if candidate_type not in CANDIDATE_TYPES:
            candidate_type = "low_risk_enhancement"
        entry = register_delivery_candidate(
            entry={
                "candidate_id": f"candidate-{intent.get('repository', 'unknown')}-{candidate_type}",
                "session_id": sid,
                "repository": intent.get("repository"),
                "candidate_type": candidate_type,
                "content": intent.get("content"),
                "metadata": dict(intent.get("metadata") or {}),
                "selection_status": "SELECTED",
            }
        )
        return {"action": "candidate", "candidate": entry}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in REAL_WORLD_DELIVERY_PROOF_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_real_world_delivery_proof_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=sid,
            metadata=dict(intent.get("metadata") or {}),
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
