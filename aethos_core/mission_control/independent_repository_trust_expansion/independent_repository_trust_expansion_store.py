# SPDX-License-Identifier: Apache-2.0
"""FIX 187 — durable store for independent repository trust expansion."""

from __future__ import annotations

import json
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
    GOVERNANCE_MUTATION_PERFORMED_FIX_187,
    INDEPENDENT_REPOSITORY_TRUST_EXPANSION_EXECUTABLE,
    INDEPENDENT_REPOSITORY_TRUST_EXPANSION_ORIGIN,
    INDEPENDENT_REPOSITORY_TRUST_EXPANSION_RECORD_KINDS,
    INDEPENDENT_REPOSITORY_TRUST_EXPANSION_RECORD_SCHEMA_VERSION,
    MAX_INDEPENDENT_REPOSITORY_TRUST_EXPANSION_CONTENT_LEN,
    MAX_PERSISTED_INDEPENDENT_REPOSITORY_TRUST_EXPANSION_RECORDS,
    PHASE_2_REPOSITORY_ORDER,
)

_REPO_RX = re.compile(r"pilotmain/[\w.-]+", re.I)


def independent_repository_trust_expansion_records_dir() -> Path:
    root = (
        Path(__file__).resolve().parents[3]
        / "data"
        / "mission_control_independent_repository_trust_expansion"
        / "records"
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def clear_independent_repository_trust_expansion_records_for_tests() -> None:
    from aethos_core.software_delivery.test_data_guard import tests_may_clear_persisted_data

    if not tests_may_clear_persisted_data():
        return
    root = independent_repository_trust_expansion_records_dir()
    if root.exists():
        for child in root.glob("*.json"):
            child.unlink(missing_ok=True)


def list_independent_repository_trust_expansion_records(
    *,
    session_id: str | None = None,
    repository: str | None = None,
    limit: int = MAX_PERSISTED_INDEPENDENT_REPOSITORY_TRUST_EXPANSION_RECORDS,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = sorted(
        independent_repository_trust_expansion_records_dir().glob("*.json"),
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
        if repository:
            rec_repo = str(payload.get("repository") or "")
            meta_repo = str((payload.get("metadata") or {}).get("repository") or "")
            if repository not in {rec_repo, meta_repo} and repository not in str(payload.get("content") or ""):
                continue
        rows.append(payload)
    rows.sort(key=lambda r: str(r.get("recorded_at") or ""))
    if len(rows) > limit:
        rows = rows[-limit:]
    return rows


def _extract_repository(text: str) -> str:
    match = _REPO_RX.search(text or "")
    return match.group(0) if match else ""


def has_repo_expansion_approval(*, repository: str) -> bool:
    repo = (repository or "").strip()
    for record in list_independent_repository_trust_expansion_records():
        if str(record.get("kind") or "") != "repo_expansion_approval":
            continue
        rec_repo = str(record.get("repository") or "") or _extract_repository(str(record.get("content") or ""))
        if rec_repo == repo:
            return True
    return False


def has_sequence_skip_approval(*, repository: str) -> bool:
    repo = (repository or "").strip()
    for record in list_independent_repository_trust_expansion_records():
        if str(record.get("kind") or "") != "sequence_skip_approval":
            continue
        rec_repo = str(record.get("repository") or "") or _extract_repository(str(record.get("content") or ""))
        if rec_repo == repo:
            return True
    return False


def next_unapproved_phase2_repository() -> str | None:
    for repo in PHASE_2_REPOSITORY_ORDER:
        if not has_repo_expansion_approval(repository=repo):
            return repo
    return None


def append_independent_repository_trust_expansion_record(
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
    if kind_norm not in INDEPENDENT_REPOSITORY_TRUST_EXPANSION_RECORD_KINDS:
        blockers.append(f"invalid_kind:{kind_norm}")
        return None, blockers

    text = (content or "").strip()
    if not text:
        blockers.append("empty_content")
        return None, blockers
    if len(text) > MAX_INDEPENDENT_REPOSITORY_TRUST_EXPANSION_CONTENT_LEN:
        blockers.append("content_too_long")
        return None, blockers

    repo = (repository or "").strip() or _extract_repository(text)
    sid = (session_id or "default").strip()[:64] or "default"
    record: dict[str, Any] = {
        "schema_version": INDEPENDENT_REPOSITORY_TRUST_EXPANSION_RECORD_SCHEMA_VERSION,
        "record_id": f"irte-{uuid.uuid4().hex[:12]}",
        "recorded_at": datetime.now(UTC).isoformat(),
        "session_id": sid,
        "repository": repo or None,
        "kind": kind_norm,
        "author": (author or "operator").strip()[:64] or "operator",
        "content": text,
        "metadata": dict(metadata or {}),
        "executable": INDEPENDENT_REPOSITORY_TRUST_EXPANSION_EXECUTABLE,
        "direct_provider_mutation_performed": False,
        "pilot_execution_performed": False,
        "trust_transfer_enabled": False,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_187,
        "independent_repository_trust_expansion_memory_only": True,
        "trust_expansion_origin": INDEPENDENT_REPOSITORY_TRUST_EXPANSION_ORIGIN,
    }
    path = independent_repository_trust_expansion_records_dir() / f"{record['record_id']}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    _prune_old_records()
    return record, blockers


def _prune_old_records(
    *, keep: int = MAX_PERSISTED_INDEPENDENT_REPOSITORY_TRUST_EXPANSION_RECORDS
) -> int:
    paths = sorted(
        independent_repository_trust_expansion_records_dir().glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    removed = 0
    for path in paths[keep:]:
        path.unlink(missing_ok=True)
        removed += 1
    return removed
