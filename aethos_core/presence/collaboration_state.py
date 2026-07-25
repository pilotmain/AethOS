# SPDX-License-Identifier: Apache-2.0
"""Collaboration state — human collaboration context."""

from __future__ import annotations

import json
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.presence.paths import presence_memory_root


def _path():
    return presence_memory_root() / "collaboration_state.json"


def _load() -> dict[str, Any]:
    path = _path()
    if not path.is_file():
        return {"sessions": {}, "focus": None}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"sessions": {}, "focus": None}


def _save(data: dict[str, Any]) -> None:
    _path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def start_collaboration_session(
    *,
    operator_id: str = "default",
    focus: str | None = None,
    investigation: str | None = None,
) -> dict[str, Any]:
    session_id = f"collab-{uuid4().hex[:10]}"
    record = {
        "session_id": session_id,
        "operator_id": operator_id,
        "focus": focus,
        "investigation": investigation,
        "started_at": time(),
        "status": "active",
    }
    data = _load()
    sessions = dict(data.get("sessions") or {})
    sessions[session_id] = record
    data["sessions"] = sessions
    if focus:
        data["focus"] = {"mode": focus, "investigation": investigation, "at": time(), "operator_id": operator_id}
    _save(data)
    return record


def get_collaboration_focus(*, operator_id: str = "default") -> dict[str, Any] | None:
    data = _load()
    focus = data.get("focus")
    if focus and focus.get("operator_id") in (operator_id, "default", None):
        return focus
    return focus


def list_collaboration_sessions(*, limit: int = 10) -> list[dict[str, Any]]:
    sessions = list((_load().get("sessions") or {}).values())
    sessions.sort(key=lambda s: float(s.get("started_at") or 0), reverse=True)
    return sessions[:limit]


def clear_collaboration_state_for_tests() -> None:
    path = _path()
    if path.is_file():
        path.unlink()
