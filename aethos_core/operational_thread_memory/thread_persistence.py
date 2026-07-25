# SPDX-License-Identifier: Apache-2.0
"""Persist operational thread state per session."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from aethos_core.operational_thread_memory.thread_state import OperationalThreadState

_MEMORY: dict[str, OperationalThreadState] = {}
DEFAULT_TTL_HOURS = 8


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "operational_threads"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_path(session_id: str) -> Path:
    safe = (session_id or "default").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def _expires_at(hours: int = DEFAULT_TTL_HOURS) -> str:
    return (datetime.now(UTC) + timedelta(hours=hours)).isoformat()


def is_thread_expired(state: OperationalThreadState | None) -> bool:
    if state is None or not state.expires_at:
        return False
    try:
        deadline = datetime.fromisoformat(state.expires_at.replace("Z", "+00:00"))
    except ValueError:
        return True
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=UTC)
    return datetime.now(UTC) >= deadline


def save_thread_state(state: OperationalThreadState) -> dict[str, Any]:
    _MEMORY[state.session_id] = state
    path = _session_path(state.session_id)
    path.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")
    return {"ok": True, "session_id": state.session_id}


def load_thread_state(*, session_id: str) -> OperationalThreadState | None:
    session_id = (session_id or "default").strip()
    cached = _MEMORY.get(session_id)
    if cached is not None:
        if is_thread_expired(cached):
            clear_thread_state(session_id=session_id)
            return None
        return cached
    path = _session_path(session_id)
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    state = OperationalThreadState.from_dict(raw)
    if is_thread_expired(state):
        clear_thread_state(session_id=session_id)
        return None
    _MEMORY[session_id] = state
    return state


def get_active_thread(*, session_id: str) -> OperationalThreadState | None:
    return load_thread_state(session_id=session_id)


def clear_thread_state(*, session_id: str) -> None:
    session_id = (session_id or "default").strip()
    _MEMORY.pop(session_id, None)
    path = _session_path(session_id)
    if path.is_file():
        path.unlink()


def clear_threads_for_tests() -> None:
    from aethos_core.task_frame.pending_action import clear_pending_actions_for_tests

    _MEMORY.clear()
    clear_pending_actions_for_tests()
    root = _store_dir()
    for path in root.glob("*.json"):
        path.unlink()
