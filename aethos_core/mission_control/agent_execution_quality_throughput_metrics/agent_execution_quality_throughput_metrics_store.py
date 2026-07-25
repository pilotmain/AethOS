# SPDX-License-Identifier: Apache-2.0
"""FIX 190 — durable store for agent execution quality and throughput metrics."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_contract import (
    AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_EXECUTABLE,
    AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_ORIGIN,
    AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_RECORD_KINDS,
    AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_RECORD_SCHEMA_VERSION,
    AGENT_METRICS_GRANT_AUTHORITY_FIX_190,
    GOVERNANCE_MUTATION_PERFORMED_FIX_190,
    MAX_AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_CONTENT_LEN,
    MAX_PERSISTED_AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_RECORDS,
)


def agent_execution_quality_throughput_metrics_records_dir() -> Path:
    root = (
        Path(__file__).resolve().parents[3]
        / "data"
        / "mission_control_agent_execution_quality_throughput_metrics"
        / "records"
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def clear_agent_execution_quality_throughput_metrics_records_for_tests() -> None:
    root = agent_execution_quality_throughput_metrics_records_dir()
    if root.exists():
        for child in root.glob("*.json"):
            child.unlink(missing_ok=True)


def list_agent_execution_quality_throughput_metrics_records(
    *,
    session_id: str | None = None,
    plan_id: str | None = None,
    limit: int = MAX_PERSISTED_AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_RECORDS,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = sorted(
        agent_execution_quality_throughput_metrics_records_dir().glob("*.json"),
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


def append_agent_execution_quality_throughput_metrics_record(
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
    if kind_norm not in AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_RECORD_KINDS:
        blockers.append(f"invalid_kind:{kind_norm}")
        return None, blockers

    text = (content or "").strip()
    if not text:
        blockers.append("empty_content")
        return None, blockers
    if len(text) > MAX_AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_CONTENT_LEN:
        blockers.append("content_too_long")
        return None, blockers

    sid = (session_id or "default").strip()[:64] or "default"
    record: dict[str, Any] = {
        "schema_version": AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_RECORD_SCHEMA_VERSION,
        "record_id": f"aetm-{uuid.uuid4().hex[:12]}",
        "recorded_at": datetime.now(UTC).isoformat(),
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "kind": kind_norm,
        "author": (author or "operator").strip()[:64] or "operator",
        "content": text,
        "metadata": dict(metadata or {}),
        "executable": AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_EXECUTABLE,
        "agent_metrics_grant_authority": AGENT_METRICS_GRANT_AUTHORITY_FIX_190,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_190,
        "agent_execution_quality_throughput_metrics_memory_only": True,
        "origin": AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_ORIGIN,
    }
    path = agent_execution_quality_throughput_metrics_records_dir() / f"{record['record_id']}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    _prune_old_records()
    return record, blockers


def _prune_old_records(
    *, keep: int = MAX_PERSISTED_AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_RECORDS
) -> int:
    paths = sorted(
        agent_execution_quality_throughput_metrics_records_dir().glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    removed = 0
    for path in paths[keep:]:
        path.unlink(missing_ok=True)
        removed += 1
    return removed
