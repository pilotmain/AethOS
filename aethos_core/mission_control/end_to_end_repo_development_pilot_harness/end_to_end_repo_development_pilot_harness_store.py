# SPDX-License-Identifier: Apache-2.0
"""FIX 181 — durable store and audit for end-to-end repo development pilot harness."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_contract import (
    END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_EXECUTABLE,
    END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_RECORD_KINDS,
    END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_RECORD_SCHEMA_VERSION,
    GOVERNANCE_MUTATION_PERFORMED_FIX_181,
    MAX_END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_CONTENT_LEN,
    MAX_PERSISTED_END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_RECORDS,
    PILOT_HARNESS_CHANNEL,
    PILOT_HARNESS_ORIGIN,
)


def end_to_end_repo_development_pilot_harness_records_dir() -> Path:
    root = (
        Path(__file__).resolve().parents[3]
        / "data"
        / "mission_control_end_to_end_repo_development_pilot_harness"
        / "records"
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def end_to_end_repo_development_pilot_harness_audit_dir() -> Path:
    root = (
        Path(__file__).resolve().parents[3]
        / "data"
        / "mission_control_end_to_end_repo_development_pilot_harness"
        / "audit"
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def clear_end_to_end_repo_development_pilot_harness_records_for_tests() -> None:
    for root in (
        end_to_end_repo_development_pilot_harness_records_dir(),
        end_to_end_repo_development_pilot_harness_audit_dir(),
    ):
        if root.exists():
            for child in root.glob("*.json"):
                child.unlink(missing_ok=True)


def list_end_to_end_repo_development_pilot_harness_records(
    *,
    session_id: str | None = None,
    plan_id: str | None = None,
    limit: int = MAX_PERSISTED_END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_RECORDS,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = sorted(
        end_to_end_repo_development_pilot_harness_records_dir().glob("*.json"),
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
        if plan_id:
            rec_plan = str(payload.get("plan_id") or "")
            if rec_plan and rec_plan != plan_id:
                continue
        rows.append(payload)
    rows.sort(key=lambda r: str(r.get("recorded_at") or ""))
    if len(rows) > limit:
        rows = rows[-limit:]
    return rows


def append_end_to_end_repo_development_pilot_harness_record(
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
    if kind_norm not in END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_RECORD_KINDS:
        blockers.append(f"invalid_kind:{kind_norm}")
        return None, blockers

    text = (content or "").strip()
    if not text:
        blockers.append("empty_content")
        return None, blockers
    if len(text) > MAX_END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_CONTENT_LEN:
        blockers.append("content_too_long")
        return None, blockers

    sid = (session_id or "default").strip()[:64] or "default"
    record: dict[str, Any] = {
        "schema_version": END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_RECORD_SCHEMA_VERSION,
        "record_id": f"e2erpdph-{uuid.uuid4().hex[:12]}",
        "recorded_at": datetime.now(UTC).isoformat(),
        "session_id": sid,
        "plan_id": plan_id or None,
        "correlation_id": correlation_id or None,
        "kind": kind_norm,
        "author": (author or "operator").strip()[:64] or "operator",
        "content": text,
        "metadata": dict(metadata or {}),
        "executable": END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_EXECUTABLE,
        "direct_provider_mutation_performed": False,
        "autonomous_pipeline_execution_performed": False,
        "hidden_command_execution_performed": False,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_181,
        "end_to_end_repo_development_pilot_harness_memory_only": True,
    }
    path = end_to_end_repo_development_pilot_harness_records_dir() / f"{record['record_id']}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    _prune_old_records()
    return record, blockers


def persist_pilot_run_audit(audit_fields: dict[str, Any]) -> dict[str, Any]:
    audit_id = f"pilot-{uuid.uuid4().hex[:12]}"
    record = {
        "audit_id": audit_id,
        "recorded_at": datetime.now(UTC).isoformat(),
        "pilot_harness_origin": PILOT_HARNESS_ORIGIN,
        "pilot_harness_channel": PILOT_HARNESS_CHANNEL,
        "direct_provider_mutation": False,
        "autonomous_pipeline_execution": False,
        **audit_fields,
    }
    path = end_to_end_repo_development_pilot_harness_audit_dir() / f"{audit_id}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def list_pilot_run_audits(*, session_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = sorted(
        end_to_end_repo_development_pilot_harness_audit_dir().glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for path in paths[:limit]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        if session_id and str(payload.get("session_id") or "") != session_id:
            continue
        rows.append(payload)
    return rows


def _prune_old_records(*, keep: int = MAX_PERSISTED_END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_RECORDS) -> int:
    paths = sorted(
        end_to_end_repo_development_pilot_harness_records_dir().glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    removed = 0
    for path in paths[keep:]:
        path.unlink(missing_ok=True)
        removed += 1
    return removed
