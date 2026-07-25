# SPDX-License-Identifier: Apache-2.0
"""Presence sessions — persistent user/session awareness."""

from __future__ import annotations

import json
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.presence.paths import presence_memory_root


def get_or_create_presence_session(*, session_id: str = "default", channel: str = "chat") -> dict[str, Any]:
    data = _load()
    sessions = dict(data.get("sessions") or {})
    row = sessions.get(session_id)
    if row:
        row["last_seen_at"] = time()
        row["channel"] = channel
        sessions[session_id] = row
        data["sessions"] = sessions
        _save(data)
        return row
    row = {
        "presence_session_id": f"psess-{uuid4().hex[:10]}",
        "session_id": session_id,
        "channel": channel,
        "created_at": time(),
        "last_seen_at": time(),
        "autonomous_execution_blocked": True,
    }
    sessions[session_id] = row
    data["sessions"] = sessions
    _save(data)
    return row


def touch_presence_session(session_id: str) -> None:
    data = _load()
    sessions = dict(data.get("sessions") or {})
    if session_id in sessions:
        sessions[session_id]["last_seen_at"] = time()
        data["sessions"] = sessions
        _save(data)


def list_presence_sessions(*, limit: int = 20) -> list[dict[str, Any]]:
    rows = list((_load().get("sessions") or {}).values())
    rows.sort(key=lambda r: float(r.get("last_seen_at") or 0), reverse=True)
    return rows[:limit]


def _path():
    return presence_memory_root() / "presence_sessions.json"


def _load() -> dict[str, Any]:
    path = _path()
    if not path.is_file():
        return {"sessions": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"sessions": {}}


def _save(data: dict[str, Any]) -> None:
    _path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def clear_presence_sessions_for_tests() -> None:
    path = _path()
    if path.is_file():
        path.unlink()
