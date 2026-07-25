# SPDX-License-Identifier: Apache-2.0
"""FIX 191 — durable store for cross-repository multi-agent delivery validation."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_contract import (
    CROSS_REPO_VALIDATION_GRANTS_TRUST_FIX_191,
    CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_EXECUTABLE,
    CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_ORIGIN,
    CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_RECORD_KINDS,
    CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_RECORD_SCHEMA_VERSION,
    GOVERNANCE_MUTATION_PERFORMED_FIX_191,
    MAX_CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_CONTENT_LEN,
    MAX_PERSISTED_CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_RECORDS,
)


def cross_repository_multi_agent_delivery_validation_records_dir() -> Path:
    root = (
        Path(__file__).resolve().parents[3]
        / "data"
        / "mission_control_cross_repository_multi_agent_delivery_validation"
        / "records"
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def clear_cross_repository_multi_agent_delivery_validation_records_for_tests() -> None:
    root = cross_repository_multi_agent_delivery_validation_records_dir()
    if root.exists():
        for child in root.glob("*.json"):
            child.unlink(missing_ok=True)


def list_cross_repository_multi_agent_delivery_validation_records(
    *,
    session_id: str | None = None,
    limit: int = MAX_PERSISTED_CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_RECORDS,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = sorted(
        cross_repository_multi_agent_delivery_validation_records_dir().glob("*.json"),
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


def append_cross_repository_multi_agent_delivery_validation_record(
    *,
    session_id: str,
    kind: str,
    content: str,
    repository: str | None = None,
    author: str = "operator",
    metadata: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    blockers: list[str] = []
    kind_norm = (kind or "").strip().lower()
    if kind_norm not in CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_RECORD_KINDS:
        blockers.append(f"invalid_kind:{kind_norm}")
        return None, blockers

    text = (content or "").strip()
    if not text:
        blockers.append("empty_content")
        return None, blockers
    if len(text) > MAX_CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_CONTENT_LEN:
        blockers.append("content_too_long")
        return None, blockers

    sid = (session_id or "default").strip()[:64] or "default"
    record: dict[str, Any] = {
        "schema_version": CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_RECORD_SCHEMA_VERSION,
        "record_id": f"crmadv-{uuid.uuid4().hex[:12]}",
        "recorded_at": datetime.now(UTC).isoformat(),
        "session_id": sid,
        "repository": repository,
        "kind": kind_norm,
        "author": (author or "operator").strip()[:64] or "operator",
        "content": text,
        "metadata": dict(metadata or {}),
        "executable": CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_EXECUTABLE,
        "cross_repo_validation_grants_trust": CROSS_REPO_VALIDATION_GRANTS_TRUST_FIX_191,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_191,
        "cross_repository_multi_agent_delivery_validation_memory_only": True,
        "origin": CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_ORIGIN,
    }
    path = cross_repository_multi_agent_delivery_validation_records_dir() / f"{record['record_id']}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    _prune_old_records()
    return record, blockers


def _prune_old_records(
    *, keep: int = MAX_PERSISTED_CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_RECORDS
) -> int:
    paths = sorted(
        cross_repository_multi_agent_delivery_validation_records_dir().glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    removed = 0
    for path in paths[keep:]:
        path.unlink(missing_ok=True)
        removed += 1
    return removed
