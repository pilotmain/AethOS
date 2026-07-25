# SPDX-License-Identifier: Apache-2.0
"""Execution locks and session-scoped execution context."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from aethos_core.providers.railway.execution_contract.execution_contract_models import (
    LOCK_STALE_SECONDS,
)
from aethos_core.providers.railway.execution_contract.execution_idempotency import (
    derive_idempotency_key,
)

_SESSION_EXECUTION: dict[str, str] = {}


def _locks_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "railway_execution_locks"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _lock_path(idempotency_key: str) -> Path:
    safe = idempotency_key.replace("/", "_")[:200]
    return _locks_dir() / f"{safe}.json"


def _now() -> datetime:
    return datetime.now(UTC)


def _parse_iso(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_execution_lock(*, idempotency_key: str) -> dict[str, Any] | None:
    path = _lock_path(idempotency_key)
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(raw) if isinstance(raw, dict) else None


def _lock_is_stale(lock: dict[str, Any]) -> bool:
    expires = _parse_iso(str(lock.get("expires_at") or ""))
    if expires is None:
        acquired = _parse_iso(str(lock.get("acquired_at") or ""))
        if acquired is None:
            return True
        return (_now() - acquired) > timedelta(seconds=LOCK_STALE_SECONDS)
    return _now() >= expires


def acquire_execution_lock(
    *,
    idempotency_key: str,
    execution_id: str,
    session_id: str,
    project: str,
    environment: str,
    service_name: str,
) -> dict[str, Any]:
    """Acquire lock or return existing active lock for the same target."""
    existing = load_execution_lock(idempotency_key=idempotency_key)
    if existing and not _lock_is_stale(existing):
        if str(existing.get("execution_id")) == execution_id:
            return {"ok": True, "lock": existing, "reused": True}
        return {
            "ok": False,
            "reason": "execution_lock_held",
            "detail": "Another execution holds the lock for this target.",
            "lock": existing,
        }

    now = _now()
    lock = {
        "lock_id": f"rlock-{uuid.uuid4().hex[:12]}",
        "idempotency_key": idempotency_key,
        "execution_id": execution_id,
        "owner_session_id": (session_id or "default").strip(),
        "project": project,
        "environment": environment,
        "service_name": service_name,
        "acquired_at": now.isoformat(),
        "expires_at": (now + timedelta(seconds=LOCK_STALE_SECONDS)).isoformat(),
    }
    try:
        _lock_path(idempotency_key).write_text(json.dumps(lock, indent=2), encoding="utf-8")
    except OSError:
        return {"ok": False, "reason": "lock_write_failed", "detail": "Could not persist execution lock."}
    return {"ok": True, "lock": lock, "reused": False}


def release_execution_lock(*, idempotency_key: str, execution_id: str) -> bool:
    existing = load_execution_lock(idempotency_key=idempotency_key)
    if not existing:
        return True
    if str(existing.get("execution_id")) != execution_id:
        return False
    try:
        _lock_path(idempotency_key).unlink(missing_ok=True)
    except OSError:
        return False
    return True


def bind_session_execution(*, session_id: str, execution_id: str) -> None:
    _SESSION_EXECUTION[(session_id or "default").strip()] = execution_id


def get_session_execution_id(*, session_id: str) -> str | None:
    return _SESSION_EXECUTION.get((session_id or "default").strip())


def resolve_execution_id_for_plan(*, session_id: str, plan: dict[str, Any]) -> str | None:
    bound = get_session_execution_id(session_id=session_id)
    if bound:
        return bound
    idempotency_key = derive_idempotency_key(plan=plan)
    lock = load_execution_lock(idempotency_key=idempotency_key)
    if lock:
        return str(lock.get("execution_id") or "") or None
    return None


def clear_for_tests() -> None:
    _SESSION_EXECUTION.clear()
    root = _locks_dir()
    for path in root.glob("*.json"):
        path.unlink()
