# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_D2 / FIX 342 — operator intent parsing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_contract import (
    MULTI_CLOUD_OPERATIONAL_PROOF_RECORD_KINDS,
)
from aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_executor import (
    run_provider_proof,
    run_wave1_provider_proof,
)
from aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_store import (
    append_multi_cloud_operational_proof_record,
)

_DASHBOARD_RX = re.compile(r"^\s*show\s+multi\s+cloud\s+dashboard\s*$", re.IGNORECASE)

_NOTE_RX = re.compile(r"^\s*provider\s+proof\s+note\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)
_REVIEW_RX = re.compile(
    r"^\s*provider\s+proof\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_RUN_WAVE_RX = re.compile(r"^\s*provider\s+proof\s+run\s+wave\s*:\s*(?P<body>.*)$", re.IGNORECASE | re.S)
_RUN_RX = re.compile(r"^\s*provider\s+proof\s+run\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)

_KV_RX = re.compile(r"(\w+)\s*=\s*([^,\s]+)")


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in _KV_RX.finditer(blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def parse_multi_cloud_operational_proof_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "multi_cloud_dashboard"}

    if _RUN_WAVE_RX.match(text):
        return {"action": "run_wave"}

    run_match = _RUN_RX.match(text)
    if run_match:
        body = (run_match.group("body") or "").strip()
        kv = _parse_kv_blob(body)
        provider = kv.get("provider") or kv.get("cloud") or ""
        if not provider:
            return None
        return {
            "action": "run",
            "provider": provider,
            "environment": kv.get("environment") or kv.get("env"),
            "service": kv.get("service"),
            "metadata": kv,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        body = (note_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "record", "kind": "provider_proof_note", "content": body}

    review_match = _REVIEW_RX.match(text)
    if review_match:
        decision = review_match.group("decision").lower()
        body = (review_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"provider_proof_review_{decision}",
            "content": body,
        }

    lowered = text.lower()
    if lowered.startswith("workstream d2:") or lowered.startswith("multi cloud proof:"):
        body = text.split(":", 1)[1].strip()
        return {"action": "record", "kind": "multi_cloud_operational_proof_record", "content": body}

    return None


def handle_multi_cloud_operational_proof_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    sid = (session_id or "default").strip()[:64] or "default"

    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "multi_cloud_dashboard"}

    if action == "run_wave":
        result = run_wave1_provider_proof(session_id=sid)
        return {"action": "run_wave", "result": result}

    if action == "run":
        result = run_provider_proof(
            session_id=sid,
            provider=str(intent.get("provider") or ""),
            environment=intent.get("environment"),
            service=intent.get("service"),
        )
        return {"action": "run", "result": result}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in MULTI_CLOUD_OPERATIONAL_PROOF_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_multi_cloud_operational_proof_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=sid,
            metadata=dict(intent.get("metadata") or {}),
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
