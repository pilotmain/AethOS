# SPDX-License-Identifier: Apache-2.0
"""FIX 180 — durable store and audit for governed chat command invocation from handoff."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_180,
    GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_EXECUTABLE,
    GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_RECORD_KINDS,
    GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_RECORD_SCHEMA_VERSION,
    GOVERNANCE_MUTATION_PERFORMED_FIX_180,
    HANDOFF_INVOCATION_CHANNEL,
    HANDOFF_INVOCATION_ORIGIN,
    MAX_GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_CONTENT_LEN,
    MAX_PERSISTED_GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_RECORDS,
)


def governed_chat_command_invocation_from_handoff_records_dir() -> Path:
    root = (
        Path(__file__).resolve().parents[3]
        / "data"
        / "mission_control_governed_chat_command_invocation_from_handoff"
        / "records"
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def governed_chat_command_invocation_from_handoff_audit_dir() -> Path:
    root = (
        Path(__file__).resolve().parents[3]
        / "data"
        / "mission_control_governed_chat_command_invocation_from_handoff"
        / "audit"
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def clear_governed_chat_command_invocation_from_handoff_records_for_tests() -> None:
    for root in (
        governed_chat_command_invocation_from_handoff_records_dir(),
        governed_chat_command_invocation_from_handoff_audit_dir(),
    ):
        if root.exists():
            for child in root.glob("*.json"):
                child.unlink(missing_ok=True)


def list_governed_chat_command_invocation_from_handoff_records(
    *,
    session_id: str | None = None,
    plan_id: str | None = None,
    limit: int = MAX_PERSISTED_GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_RECORDS,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = sorted(
        governed_chat_command_invocation_from_handoff_records_dir().glob("*.json"),
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


def append_governed_chat_command_invocation_from_handoff_record(
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
    if kind_norm not in GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_RECORD_KINDS:
        blockers.append(f"invalid_kind:{kind_norm}")
        return None, blockers

    text = (content or "").strip()
    if not text:
        blockers.append("empty_content")
        return None, blockers
    if len(text) > MAX_GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_CONTENT_LEN:
        blockers.append("content_too_long")
        return None, blockers

    sid = (session_id or "default").strip()[:64] or "default"
    record: dict[str, Any] = {
        "schema_version": GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_RECORD_SCHEMA_VERSION,
        "record_id": f"gccifh-{uuid.uuid4().hex[:12]}",
        "recorded_at": datetime.now(UTC).isoformat(),
        "session_id": sid,
        "plan_id": plan_id or None,
        "correlation_id": correlation_id or None,
        "kind": kind_norm,
        "author": (author or "operator").strip()[:64] or "operator",
        "content": text,
        "metadata": dict(metadata or {}),
        "executable": GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_EXECUTABLE,
        "direct_provider_mutation_performed": False,
        "direct_execution_performed": False,
        "hidden_command_execution_performed": False,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_180,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_180,
        "governed_chat_command_invocation_from_handoff_memory_only": True,
    }
    path = governed_chat_command_invocation_from_handoff_records_dir() / f"{record['record_id']}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    _prune_old_records()
    return record, blockers


def persist_handoff_invocation_audit(audit_fields: dict[str, Any]) -> dict[str, Any]:
    audit_id = f"hinv-{uuid.uuid4().hex[:12]}"
    record = {
        "audit_id": audit_id,
        "recorded_at": datetime.now(UTC).isoformat(),
        "handoff_invocation_origin": HANDOFF_INVOCATION_ORIGIN,
        "handoff_invocation_channel": HANDOFF_INVOCATION_CHANNEL,
        "direct_provider_mutation": False,
        **audit_fields,
    }
    path = governed_chat_command_invocation_from_handoff_audit_dir() / f"{audit_id}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def list_handoff_invocation_audits(*, session_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = sorted(
        governed_chat_command_invocation_from_handoff_audit_dir().glob("*.json"),
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


def _prune_old_records(*, keep: int = MAX_PERSISTED_GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_RECORDS) -> int:
    paths = sorted(
        governed_chat_command_invocation_from_handoff_records_dir().glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    removed = 0
    for path in paths[keep:]:
        path.unlink(missing_ok=True)
        removed += 1
    return removed
