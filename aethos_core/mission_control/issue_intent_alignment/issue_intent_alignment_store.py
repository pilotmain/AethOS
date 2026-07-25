# SPDX-License-Identifier: Apache-2.0
"""FIX 184 — durable store for issue intent alignment records."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_contract import (
    GOVERNANCE_MUTATION_PERFORMED_FIX_184,
    ISSUE_INTENT_ALIGNMENT_EXECUTABLE,
    ISSUE_INTENT_ALIGNMENT_ORIGIN,
    ISSUE_INTENT_ALIGNMENT_RECORD_KINDS,
    ISSUE_INTENT_ALIGNMENT_RECORD_SCHEMA_VERSION,
    MAX_ISSUE_INTENT_ALIGNMENT_CONTENT_LEN,
    MAX_PERSISTED_ISSUE_INTENT_ALIGNMENT_RECORDS,
)


def issue_intent_alignment_records_dir() -> Path:
    root = (
        Path(__file__).resolve().parents[3]
        / "data"
        / "mission_control_issue_intent_alignment"
        / "records"
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def clear_issue_intent_alignment_records_for_tests() -> None:
    root = issue_intent_alignment_records_dir()
    if root.exists():
        for child in root.glob("*.json"):
            child.unlink(missing_ok=True)


def list_issue_intent_alignment_records(
    *,
    session_id: str | None = None,
    plan_id: str | None = None,
    limit: int = MAX_PERSISTED_ISSUE_INTENT_ALIGNMENT_RECORDS,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = sorted(
        issue_intent_alignment_records_dir().glob("*.json"),
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


def append_issue_intent_alignment_record(
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
    if kind_norm not in ISSUE_INTENT_ALIGNMENT_RECORD_KINDS:
        blockers.append(f"invalid_kind:{kind_norm}")
        return None, blockers

    text = (content or "").strip()
    if not text:
        blockers.append("empty_content")
        return None, blockers
    if len(text) > MAX_ISSUE_INTENT_ALIGNMENT_CONTENT_LEN:
        blockers.append("content_too_long")
        return None, blockers

    sid = (session_id or "default").strip()[:64] or "default"
    record: dict[str, Any] = {
        "schema_version": ISSUE_INTENT_ALIGNMENT_RECORD_SCHEMA_VERSION,
        "record_id": f"iia-{uuid.uuid4().hex[:12]}",
        "recorded_at": datetime.now(UTC).isoformat(),
        "session_id": sid,
        "plan_id": plan_id or None,
        "correlation_id": correlation_id or None,
        "kind": kind_norm,
        "author": (author or "operator").strip()[:64] or "operator",
        "content": text,
        "metadata": dict(metadata or {}),
        "executable": ISSUE_INTENT_ALIGNMENT_EXECUTABLE,
        "patch_execution_performed": False,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_184,
        "issue_intent_alignment_memory_only": True,
        "alignment_origin": ISSUE_INTENT_ALIGNMENT_ORIGIN,
    }
    path = issue_intent_alignment_records_dir() / f"{record['record_id']}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    _prune_old_records()
    return record, blockers


def _prune_old_records(*, keep: int = MAX_PERSISTED_ISSUE_INTENT_ALIGNMENT_RECORDS) -> int:
    paths = sorted(
        issue_intent_alignment_records_dir().glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    removed = 0
    for path in paths[keep:]:
        path.unlink(missing_ok=True)
        removed += 1
    return removed
