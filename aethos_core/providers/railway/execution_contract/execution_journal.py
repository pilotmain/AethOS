# SPDX-License-Identifier: Apache-2.0
"""Persist Railway execution journals under data/railway_execution_journal/."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.providers.railway.execution_contract.execution_contract_models import (
    EXECUTION_ENABLED,
)
from aethos_core.providers.railway.execution_contract.execution_idempotency import (
    derive_idempotency_key,
)

_INDEX_FILENAME = "execution_journal_index.json"
_MEMORY: dict[str, dict[str, Any]] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "railway_execution_journal"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _journal_path(execution_id: str) -> Path:
    safe = (execution_id or "").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def _index_path() -> Path:
    return _store_dir() / _INDEX_FILENAME


def _read_index() -> dict[str, Any]:
    path = _index_path()
    if not path.is_file():
        return {"by_idempotency": {}, "by_execution_id": {}}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"by_idempotency": {}, "by_execution_id": {}}
    if not isinstance(raw, dict):
        return {"by_idempotency": {}, "by_execution_id": {}}
    raw.setdefault("by_idempotency", {})
    raw.setdefault("by_execution_id", {})
    return raw


def _write_index(index: dict[str, Any]) -> None:
    try:
        _index_path().write_text(json.dumps(index, indent=2), encoding="utf-8")
    except OSError:
        pass


def _persist_journal(journal: dict[str, Any]) -> dict[str, Any]:
    execution_id = str(journal.get("execution_id") or "")
    if not execution_id:
        return journal
    _MEMORY[execution_id] = journal
    try:
        _journal_path(execution_id).write_text(json.dumps(journal, indent=2), encoding="utf-8")
    except OSError:
        pass
    index = _read_index()
    idem = str(journal.get("idempotency_key") or "")
    if idem:
        index["by_idempotency"][idem] = execution_id
    index["by_execution_id"][execution_id] = idem
    _write_index(index)
    return journal


def load_latest_journal_for_session(*, session_id: str) -> dict[str, Any] | None:
    """Most recent journal for a chat session — used to rebuild deploy follow-up context."""
    session_id = (session_id or "default").strip()
    latest: dict[str, Any] | None = None
    latest_ts = ""
    for path in _store_dir().glob("*.json"):
        if path.name == _INDEX_FILENAME:
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(raw, dict):
            continue
        if str(raw.get("session_id") or "") != session_id:
            continue
        if not raw.get("railway_service_id"):
            continue
        updated = str(raw.get("updated_at") or raw.get("created_at") or "")
        if latest is None or updated >= latest_ts:
            latest = dict(raw)
            latest_ts = updated
    return latest


def load_journal_by_id(execution_id: str) -> dict[str, Any] | None:
    execution_id = (execution_id or "").strip()
    if not execution_id:
        return None
    cached = _MEMORY.get(execution_id)
    if cached is not None:
        return dict(cached)
    path = _journal_path(execution_id)
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(raw, dict) and raw.get("execution_id"):
        _MEMORY[execution_id] = dict(raw)
        return dict(raw)
    return None


def load_journal_by_idempotency_key(idempotency_key: str) -> dict[str, Any] | None:
    idempotency_key = (idempotency_key or "").strip()
    if not idempotency_key:
        return None
    index = _read_index()
    execution_id = str((index.get("by_idempotency") or {}).get(idempotency_key) or "")
    if execution_id:
        return load_journal_by_id(execution_id)
    for path in _store_dir().glob("*.json"):
        if path.name == _INDEX_FILENAME:
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(raw, dict) and raw.get("idempotency_key") == idempotency_key:
            return dict(raw)
    return None


def new_execution_journal(
    *,
    plan: dict[str, Any],
    session_id: str,
    initial_state: str = "draft",
    approval: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = datetime.now(UTC).isoformat()
    idempotency_key = derive_idempotency_key(plan=plan)
    journal = {
        "execution_id": f"rexec-{uuid.uuid4().hex[:12]}",
        "plan_id": str(plan.get("plan_id") or ""),
        "session_id": (session_id or "default").strip(),
        "repo": str(plan.get("repo") or ""),
        "branch": str(plan.get("branch") or "main"),
        "project": str(plan.get("project") or ""),
        "environment": str(plan.get("environment") or ""),
        "service_name": str(plan.get("service_name") or ""),
        "deploy_component": str(plan.get("deploy_component") or "api"),
        "root_directory": str(plan.get("root_directory") or ""),
        "created_at": now,
        "updated_at": now,
        "state": initial_state,
        "state_history": [],
        "phases": [],
        "idempotency_key": idempotency_key,
        "mutation_enabled": EXECUTION_ENABLED,
        "rollback_ready": True,
        "rollback_available": False,
        "approval": dict(approval or {}),
    }
    return _persist_journal(journal)


def save_execution_journal(journal: dict[str, Any]) -> dict[str, Any]:
    payload = dict(journal)
    payload["updated_at"] = datetime.now(UTC).isoformat()
    return _persist_journal(payload)


def get_or_create_execution_journal(
    *,
    plan: dict[str, Any],
    session_id: str,
    initial_state: str = "draft",
    approval: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], bool]:
    """Return (journal, created). Reuses journal when idempotency key matches."""
    idempotency_key = derive_idempotency_key(plan=plan)
    existing = load_journal_by_idempotency_key(idempotency_key)
    if existing:
        return dict(existing), False
    return new_execution_journal(
        plan=plan,
        session_id=session_id,
        initial_state=initial_state,
        approval=approval,
    ), True


def append_phase_record(
    journal: dict[str, Any],
    *,
    phase: str,
    status: str,
    detail: str = "",
) -> dict[str, Any]:
    updated = dict(journal)
    phases = list(updated.get("phases") or [])
    phases.append(
        {
            "phase": phase,
            "status": status,
            "detail": detail,
            "recorded_at": datetime.now(UTC).isoformat(),
        }
    )
    updated["phases"] = phases
    return save_execution_journal(updated)


def clear_for_tests() -> None:
    _MEMORY.clear()
    root = _store_dir()
    for path in root.glob("*.json"):
        path.unlink()
