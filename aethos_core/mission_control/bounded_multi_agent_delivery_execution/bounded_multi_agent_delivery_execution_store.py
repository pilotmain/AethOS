# SPDX-License-Identifier: Apache-2.0
"""FIX 189 — durable store for bounded multi-agent delivery execution."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_contract import (
    AGENT_EXECUTION_AUTHORITY_FIX_189,
    BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_EXECUTABLE,
    BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_ORIGIN,
    BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_RECORD_KINDS,
    BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_RECORD_SCHEMA_VERSION,
    GOVERNANCE_MUTATION_PERFORMED_FIX_189,
    MAX_BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_CONTENT_LEN,
    MAX_PERSISTED_BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_RECORDS,
    MERGE_AUTHORITY_FIX_189,
    PROVIDER_AUTHORITY_FIX_189,
    RAILWAY_AUTHORITY_FIX_189,
)


def bounded_multi_agent_delivery_execution_records_dir() -> Path:
    root = (
        Path(__file__).resolve().parents[3]
        / "data"
        / "mission_control_bounded_multi_agent_delivery_execution"
        / "records"
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def clear_bounded_multi_agent_delivery_execution_records_for_tests() -> None:
    root = bounded_multi_agent_delivery_execution_records_dir()
    if root.exists():
        for child in root.glob("*.json"):
            child.unlink(missing_ok=True)


def list_bounded_multi_agent_delivery_execution_records(
    *,
    session_id: str | None = None,
    plan_id: str | None = None,
    limit: int = MAX_PERSISTED_BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_RECORDS,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = sorted(
        bounded_multi_agent_delivery_execution_records_dir().glob("*.json"),
        key=lambda p: p.stat().st_mtime,
    )
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        if session_id and str(payload.get("session_id") or "") != session_id:
            continue
        if plan_id and str(payload.get("plan_id") or "") != plan_id:
            continue
        rows.append(payload)
    rows.sort(key=lambda r: str(r.get("recorded_at") or ""))
    if len(rows) > limit:
        rows = rows[-limit:]
    return rows


def list_agent_execution_receipts(
    *,
    session_id: str,
    plan_id: str | None = None,
) -> list[dict[str, Any]]:
    return [
        r
        for r in list_bounded_multi_agent_delivery_execution_records(session_id=session_id, plan_id=plan_id)
        if str(r.get("kind") or "") == "agent_execution_receipt"
    ]


def append_bounded_multi_agent_delivery_execution_record(
    *,
    session_id: str,
    kind: str,
    content: str,
    plan_id: str | None = None,
    correlation_id: str | None = None,
    author: str = "operator",
    metadata: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    blockers: list[str] = []
    kind_norm = (kind or "").strip().lower()
    if kind_norm not in BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_RECORD_KINDS:
        blockers.append(f"invalid_kind:{kind_norm}")
        return None, blockers

    text = (content or "").strip()
    if not text and kind_norm not in ("pipeline_transition", "agent_execution_receipt"):
        blockers.append("empty_content")
        return None, blockers
    if len(text) > MAX_BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_CONTENT_LEN:
        blockers.append("content_too_long")
        return None, blockers

    sid = (session_id or "default").strip()[:64] or "default"
    record: dict[str, Any] = {
        "schema_version": BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_RECORD_SCHEMA_VERSION,
        "record_id": f"bmade-{uuid.uuid4().hex[:12]}",
        "recorded_at": datetime.now(UTC).isoformat(),
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "kind": kind_norm,
        "author": (author or "operator").strip()[:64] or "operator",
        "content": text,
        "metadata": dict(metadata or {}),
        "executable": BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_EXECUTABLE,
        "agent_execution_authority": AGENT_EXECUTION_AUTHORITY_FIX_189,
        "merge_authority": MERGE_AUTHORITY_FIX_189,
        "railway_authority": RAILWAY_AUTHORITY_FIX_189,
        "provider_authority": PROVIDER_AUTHORITY_FIX_189,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_189,
        "bounded_multi_agent_delivery_execution_memory_only": True,
        "origin": BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_ORIGIN,
    }
    path = bounded_multi_agent_delivery_execution_records_dir() / f"{record['record_id']}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    _prune_old_records()
    return record, blockers


def _prune_old_records(
    *, keep: int = MAX_PERSISTED_BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_RECORDS
) -> int:
    paths = sorted(
        bounded_multi_agent_delivery_execution_records_dir().glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    removed = 0
    for path in paths[keep:]:
        path.unlink(missing_ok=True)
        removed += 1
    return removed
