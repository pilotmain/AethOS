# SPDX-License-Identifier: Apache-2.0
"""FIX 200 — durable store for governed merge lifecycle."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_contract import (
    AUTONOMOUS_MERGE_ENABLED_FIX_200,
    GOVERNANCE_MUTATION_PERFORMED_FIX_200,
    GOVERNED_MERGE_LIFECYCLE_EXECUTABLE,
    GOVERNED_MERGE_LIFECYCLE_ORIGIN,
    GOVERNED_MERGE_LIFECYCLE_RECORD_KINDS,
    GOVERNED_MERGE_LIFECYCLE_RECORD_SCHEMA_VERSION,
    MAX_GOVERNED_MERGE_LIFECYCLE_CONTENT_LEN,
    MAX_PERSISTED_GOVERNED_MERGE_LIFECYCLE_RECORDS,
    MERGE_AUTHORITY_FIX_200,
    MERGE_DECISION_KINDS,
)


def governed_merge_lifecycle_records_dir() -> Path:
    root = (
        Path(__file__).resolve().parents[3]
        / "data"
        / "mission_control_governed_merge_lifecycle"
        / "records"
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def clear_governed_merge_lifecycle_records_for_tests() -> None:
    root = governed_merge_lifecycle_records_dir()
    if root.exists():
        for child in root.glob("*.json"):
            child.unlink(missing_ok=True)


def list_governed_merge_lifecycle_records(
    *,
    session_id: str | None = None,
    plan_id: str | None = None,
    limit: int = MAX_PERSISTED_GOVERNED_MERGE_LIFECYCLE_RECORDS,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = sorted(
        governed_merge_lifecycle_records_dir().glob("*.json"),
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


def latest_merge_decision_record(
    *,
    session_id: str,
    plan_id: str | None = None,
) -> dict[str, Any] | None:
    decisions = [
        r
        for r in list_governed_merge_lifecycle_records(session_id=session_id, plan_id=plan_id)
        if str(r.get("kind") or "") in MERGE_DECISION_KINDS
    ]
    return decisions[-1] if decisions else None


def merge_decision_status(*, session_id: str, plan_id: str | None = None) -> str | None:
    record = latest_merge_decision_record(session_id=session_id, plan_id=plan_id)
    if not record:
        return None
    kind = str(record.get("kind") or "")
    if kind == "merge_decision_approve":
        return "approve"
    if kind == "merge_decision_hold":
        return "hold"
    if kind == "merge_decision_reject":
        return "reject"
    return None


def append_governed_merge_lifecycle_record(
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
    if kind_norm not in GOVERNED_MERGE_LIFECYCLE_RECORD_KINDS:
        blockers.append(f"invalid_kind:{kind_norm}")
        return None, blockers

    text = (content or "").strip()
    if not text:
        blockers.append("empty_content")
        return None, blockers
    if len(text) > MAX_GOVERNED_MERGE_LIFECYCLE_CONTENT_LEN:
        blockers.append("content_too_long")
        return None, blockers

    sid = (session_id or "default").strip()[:64] or "default"
    record: dict[str, Any] = {
        "schema_version": GOVERNED_MERGE_LIFECYCLE_RECORD_SCHEMA_VERSION,
        "record_id": f"gml-{uuid.uuid4().hex[:12]}",
        "recorded_at": datetime.now(UTC).isoformat(),
        "session_id": sid,
        "plan_id": plan_id,
        "kind": kind_norm,
        "author": (author or "operator").strip()[:64] or "operator",
        "content": text,
        "metadata": dict(metadata or {}),
        "executable": GOVERNED_MERGE_LIFECYCLE_EXECUTABLE,
        "merge_authority": MERGE_AUTHORITY_FIX_200,
        "autonomous_merge_enabled": AUTONOMOUS_MERGE_ENABLED_FIX_200,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_200,
        "governed_merge_lifecycle_memory_only": True,
        "origin": GOVERNED_MERGE_LIFECYCLE_ORIGIN,
    }
    path = governed_merge_lifecycle_records_dir() / f"{record['record_id']}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    _prune_old_records()
    return record, blockers


def _prune_old_records(*, keep: int = MAX_PERSISTED_GOVERNED_MERGE_LIFECYCLE_RECORDS) -> int:
    paths = sorted(
        governed_merge_lifecycle_records_dir().glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    removed = 0
    for path in paths[keep:]:
        path.unlink(missing_ok=True)
        removed += 1
    return removed
