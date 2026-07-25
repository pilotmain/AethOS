# SPDX-License-Identifier: Apache-2.0
"""FIX 250 — durable store for governed application generation."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.mission_control.governed_application_generation.governed_application_generation_contract import (
    APPLICATION_GENERATION_AUTHORITY_FIX_250,
    GENERATION_DECISION_KINDS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_250,
    GOVERNED_APPLICATION_GENERATION_EXECUTABLE,
    GOVERNED_APPLICATION_GENERATION_ORIGIN,
    GOVERNED_APPLICATION_GENERATION_RECORD_KINDS,
    GOVERNED_APPLICATION_GENERATION_RECORD_SCHEMA_VERSION,
    GITHUB_MUTATION_AUTHORITY_FIX_250,
    MAX_GOVERNED_APPLICATION_GENERATION_CONTENT_LEN,
    MAX_PERSISTED_GOVERNED_APPLICATION_GENERATION_RECORDS,
    REPOSITORY_CREATION_AUTHORITY_FIX_250,
)


def governed_application_generation_records_dir() -> Path:
    root = (
        Path(__file__).resolve().parents[3]
        / "data"
        / "mission_control_governed_application_generation"
        / "records"
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def clear_governed_application_generation_records_for_tests() -> None:
    root = governed_application_generation_records_dir()
    if root.exists():
        for child in root.glob("*.json"):
            child.unlink(missing_ok=True)


def list_governed_application_generation_records(
    *,
    session_id: str | None = None,
    limit: int = MAX_PERSISTED_GOVERNED_APPLICATION_GENERATION_RECORDS,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = sorted(
        governed_application_generation_records_dir().glob("*.json"),
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
        rows.append(payload)
    rows.sort(key=lambda r: str(r.get("recorded_at") or ""))
    if len(rows) > limit:
        rows = rows[-limit:]
    return rows


def latest_generation_decision_record(*, session_id: str) -> dict[str, Any] | None:
    decisions = [
        r
        for r in list_governed_application_generation_records(session_id=session_id)
        if str(r.get("kind") or "") in GENERATION_DECISION_KINDS
    ]
    return decisions[-1] if decisions else None


def generation_decision_status(*, session_id: str) -> str | None:
    record = latest_generation_decision_record(session_id=session_id)
    if not record:
        return None
    kind = str(record.get("kind") or "")
    if kind == "generation_decision_approve":
        return "approve"
    if kind == "generation_decision_hold":
        return "hold"
    if kind == "generation_decision_reject":
        return "reject"
    return None


def latest_record_by_kind(*, session_id: str, kind: str) -> dict[str, Any] | None:
    rows = [
        r
        for r in list_governed_application_generation_records(session_id=session_id)
        if str(r.get("kind") or "") == kind
    ]
    return rows[-1] if rows else None


def append_governed_application_generation_record(
    *,
    session_id: str,
    kind: str,
    content: str,
    author: str = "operator",
    metadata: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    blockers: list[str] = []
    kind_norm = (kind or "").strip().lower()
    if kind_norm not in GOVERNED_APPLICATION_GENERATION_RECORD_KINDS:
        blockers.append(f"invalid_kind:{kind_norm}")
        return None, blockers

    text = (content or "").strip()
    if not text:
        blockers.append("empty_content")
        return None, blockers
    if len(text) > MAX_GOVERNED_APPLICATION_GENERATION_CONTENT_LEN:
        blockers.append("content_too_long")
        return None, blockers

    sid = (session_id or "default").strip()[:64] or "default"
    record: dict[str, Any] = {
        "schema_version": GOVERNED_APPLICATION_GENERATION_RECORD_SCHEMA_VERSION,
        "record_id": f"gag-{uuid.uuid4().hex[:12]}",
        "recorded_at": datetime.now(UTC).isoformat(),
        "session_id": sid,
        "kind": kind_norm,
        "author": (author or "operator").strip()[:64] or "operator",
        "content": text,
        "metadata": dict(metadata or {}),
        "executable": GOVERNED_APPLICATION_GENERATION_EXECUTABLE,
        "application_generation_authority": APPLICATION_GENERATION_AUTHORITY_FIX_250,
        "repository_creation_authority": REPOSITORY_CREATION_AUTHORITY_FIX_250,
        "github_mutation_authority": GITHUB_MUTATION_AUTHORITY_FIX_250,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_250,
        "governed_application_generation_memory_only": True,
        "origin": GOVERNED_APPLICATION_GENERATION_ORIGIN,
    }
    path = governed_application_generation_records_dir() / f"{record['record_id']}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    _prune_old_records()
    return record, blockers


def _prune_old_records(*, keep: int = MAX_PERSISTED_GOVERNED_APPLICATION_GENERATION_RECORDS) -> int:
    paths = sorted(
        governed_application_generation_records_dir().glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    removed = 0
    for path in paths[keep:]:
        path.unlink(missing_ok=True)
        removed += 1
    return removed
