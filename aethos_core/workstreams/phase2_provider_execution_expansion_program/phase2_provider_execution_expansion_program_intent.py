# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_D1 / FIX 341 — operator intent parsing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.phase2_provider_execution_expansion_program.phase2_provider_execution_expansion_program_contract import (
    PHASE2_PROVIDER_EXECUTION_EXPANSION_RECORD_KINDS,
)
from aethos_core.workstreams.phase2_provider_execution_expansion_program.phase2_provider_execution_expansion_program_executor import (
    execute_phase2_provider_deployment,
)
from aethos_core.workstreams.phase2_provider_execution_expansion_program.phase2_provider_execution_expansion_program_store import (
    _normalize_provider,
    append_phase2_provider_execution_expansion_record,
)

_DASHBOARD_RX = re.compile(r"^\s*show\s+phase2\s+provider\s+dashboard\s*$", re.IGNORECASE)

_NOTE_RX = re.compile(r"^\s*phase2\s+provider\s+(?:expansion\s+)?note\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)
_READINESS_RX = re.compile(
    r"^\s*phase2\s+provider\s+readiness\s+review\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_EXECUTION_RX = re.compile(
    r"^\s*phase2\s+provider\s+execution\s+review\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_REVIEW_RX = re.compile(
    r"^\s*phase2\s+provider\s+expansion\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_DEPLOY_RX = re.compile(
    r"^\s*phase2\s+provider\s+deploy\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)

_KV_RX = re.compile(r"(\w+)\s*=\s*([^,\s]+)")


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in _KV_RX.finditer(blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def parse_phase2_provider_execution_expansion_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "expansion_dashboard"}

    deploy_match = _DEPLOY_RX.match(text)
    if deploy_match:
        body = (deploy_match.group("body") or "").strip()
        kv = _parse_kv_blob(body)
        provider = kv.get("provider") or ""
        if not _normalize_provider(provider):
            return None
        return {
            "action": "deploy",
            "provider": provider,
            "service": kv.get("service"),
            "environment": kv.get("environment") or kv.get("env") or "staging",
            "target": kv.get("target"),
            "metadata": kv,
        }

    for rx, kind in (
        (_READINESS_RX, "phase2_provider_readiness_review_note"),
        (_EXECUTION_RX, "phase2_provider_execution_review_note"),
    ):
        match = rx.match(text)
        if match:
            body = (match.group("body") or "").strip()
            kv = _parse_kv_blob(body)
            return {
                "action": "record",
                "kind": kind,
                "content": body,
                "metadata": {
                    "provider": _normalize_provider(kv.get("provider")),
                    "service": kv.get("service"),
                    "environment": kv.get("environment") or kv.get("env"),
                },
            }

    note_match = _NOTE_RX.match(text)
    if note_match:
        body = (note_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "record", "kind": "phase2_provider_expansion_note", "content": body}

    review_match = _REVIEW_RX.match(text)
    if review_match:
        decision = review_match.group("decision").lower()
        body = (review_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"phase2_provider_expansion_review_{decision}",
            "content": body,
        }

    lowered = text.lower()
    if lowered.startswith("workstream d1:") or lowered.startswith("phase2 provider:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "phase2_provider_execution_expansion_record",
            "content": body,
        }

    return None


def handle_phase2_provider_execution_expansion_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    sid = (session_id or "default").strip()[:64] or "default"

    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "expansion_dashboard"}

    if action == "deploy":
        result = execute_phase2_provider_deployment(
            session_id=sid,
            provider=str(intent.get("provider") or ""),
            service=intent.get("service"),
            environment=str(intent.get("environment") or "staging"),
            target=intent.get("target"),
        )
        return {"action": "deploy", "result": result}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in PHASE2_PROVIDER_EXECUTION_EXPANSION_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_phase2_provider_execution_expansion_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=sid,
            metadata=dict(intent.get("metadata") or {}),
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
