# SPDX-License-Identifier: Apache-2.0
"""FIX 220 — durable store for governed monitoring lifecycle."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_contract import (
    AUTONOMOUS_REMEDIATION_ENABLED_FIX_220,
    GOVERNANCE_MUTATION_PERFORMED_FIX_220,
    GOVERNED_MONITORING_LIFECYCLE_EXECUTABLE,
    GOVERNED_MONITORING_LIFECYCLE_ORIGIN,
    GOVERNED_MONITORING_LIFECYCLE_RECORD_KINDS,
    GOVERNED_MONITORING_LIFECYCLE_RECORD_SCHEMA_VERSION,
    MAX_GOVERNED_MONITORING_LIFECYCLE_CONTENT_LEN,
    MAX_PERSISTED_GOVERNED_MONITORING_LIFECYCLE_RECORDS,
    MONITORING_AUTHORITY_FIX_220,
    OPERATIONAL_DECISION_KINDS,
)


def governed_monitoring_lifecycle_records_dir() -> Path:
    root = (
        Path(__file__).resolve().parents[3]
        / "data"
        / "mission_control_governed_monitoring_lifecycle"
        / "records"
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def clear_governed_monitoring_lifecycle_records_for_tests() -> None:
    root = governed_monitoring_lifecycle_records_dir()
    if root.exists():
        for child in root.glob("*.json"):
            child.unlink(missing_ok=True)


def list_governed_monitoring_lifecycle_records(
    *,
    session_id: str | None = None,
    plan_id: str | None = None,
    limit: int = MAX_PERSISTED_GOVERNED_MONITORING_LIFECYCLE_RECORDS,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = sorted(
        governed_monitoring_lifecycle_records_dir().glob("*.json"),
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


def latest_operational_decision_record(
    *,
    session_id: str,
    plan_id: str | None = None,
) -> dict[str, Any] | None:
    decisions = [
        r
        for r in list_governed_monitoring_lifecycle_records(session_id=session_id, plan_id=plan_id)
        if str(r.get("kind") or "") in OPERATIONAL_DECISION_KINDS
    ]
    return decisions[-1] if decisions else None


def operational_decision_status(*, session_id: str, plan_id: str | None = None) -> str | None:
    record = latest_operational_decision_record(session_id=session_id, plan_id=plan_id)
    if not record:
        return None
    kind = str(record.get("kind") or "")
    if kind == "operational_decision_continue":
        return "continue"
    if kind == "operational_decision_investigate":
        return "investigate"
    if kind == "operational_decision_escalate":
        return "escalate"
    if kind == "operational_decision_ignore":
        return "ignore"
    return None


def append_governed_monitoring_lifecycle_record(
    *,
    session_id: str,
    kind: str,
    content: str,
    plan_id: str | None = None,
    author: str = "operator",
    metadata: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    blockers: list[str] = []
    kind_norm = (kind or "").strip().lower()
    if kind_norm not in GOVERNED_MONITORING_LIFECYCLE_RECORD_KINDS:
        blockers.append(f"invalid_kind:{kind_norm}")
        return None, blockers

    text = (content or "").strip()
    if not text:
        blockers.append("empty_content")
        return None, blockers
    if len(text) > MAX_GOVERNED_MONITORING_LIFECYCLE_CONTENT_LEN:
        blockers.append("content_too_long")
        return None, blockers

    sid = (session_id or "default").strip()[:64] or "default"
    record: dict[str, Any] = {
        "schema_version": GOVERNED_MONITORING_LIFECYCLE_RECORD_SCHEMA_VERSION,
        "record_id": f"gmlc-{uuid.uuid4().hex[:12]}",
        "recorded_at": datetime.now(UTC).isoformat(),
        "session_id": sid,
        "plan_id": plan_id,
        "kind": kind_norm,
        "author": (author or "operator").strip()[:64] or "operator",
        "content": text,
        "metadata": dict(metadata or {}),
        "executable": GOVERNED_MONITORING_LIFECYCLE_EXECUTABLE,
        "monitoring_authority": MONITORING_AUTHORITY_FIX_220,
        "autonomous_remediation_enabled": AUTONOMOUS_REMEDIATION_ENABLED_FIX_220,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_220,
        "governed_monitoring_lifecycle_memory_only": True,
        "origin": GOVERNED_MONITORING_LIFECYCLE_ORIGIN,
    }
    path = governed_monitoring_lifecycle_records_dir() / f"{record['record_id']}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    _prune_old_records()
    return record, blockers


def _prune_old_records(*, keep: int = MAX_PERSISTED_GOVERNED_MONITORING_LIFECYCLE_RECORDS) -> int:
    paths = sorted(
        governed_monitoring_lifecycle_records_dir().glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    removed = 0
    for path in paths[keep:]:
        path.unlink(missing_ok=True)
        removed += 1
    return removed
