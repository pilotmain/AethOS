# SPDX-License-Identifier: Apache-2.0
"""Persist active task frames per session."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.task_frame.task_expiration import is_task_frame_expired
from aethos_core.task_frame.task_frame import TaskFrame

_MEMORY: dict[str, TaskFrame] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "task_frames"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_path(session_id: str) -> Path:
    safe = (session_id or "default").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def save_task_frame(frame: TaskFrame) -> dict[str, Any]:
    _MEMORY[frame.session_id] = frame
    path = _session_path(frame.session_id)
    path.write_text(json.dumps(frame.to_dict(), indent=2), encoding="utf-8")
    return {"ok": True, "task_id": frame.task_id, "path": str(path)}


def load_task_frame(*, session_id: str) -> TaskFrame | None:
    session_id = (session_id or "default").strip()
    cached = _MEMORY.get(session_id)
    if cached is not None:
        if is_task_frame_expired(cached.expires_at):
            clear_task_frame(session_id=session_id)
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
    frame = TaskFrame.from_dict(raw)
    if is_task_frame_expired(frame.expires_at):
        clear_task_frame(session_id=session_id)
        return None
    _MEMORY[session_id] = frame
    return frame


def get_active_task_frame(*, session_id: str) -> TaskFrame | None:
    frame = load_task_frame(session_id=session_id)
    if frame is None:
        return None
    if frame.status in {"completed", "cancelled", "expired"}:
        return None
    return frame


def clear_task_frame(*, session_id: str) -> None:
    session_id = (session_id or "default").strip()
    _MEMORY.pop(session_id, None)
    path = _session_path(session_id)
    if path.is_file():
        path.unlink()


def complete_task_frame(*, session_id: str, status: str = "completed") -> None:
    frame = load_task_frame(session_id=session_id)
    if frame is None:
        return
    frame.status = status
    frame.updated_at = datetime.now(UTC).isoformat()
    save_task_frame(frame)


def clear_task_frames_for_tests() -> None:
    _MEMORY.clear()
    root = _store_dir()
    for path in root.glob("*.json"):
        path.unlink()
