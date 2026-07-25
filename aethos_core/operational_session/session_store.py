# SPDX-License-Identifier: Apache-2.0
"""Persist operational sessions per chat session."""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path

from aethos_core.operational_session.session_context import SessionContext
from aethos_core.operational_session.session_subject import SessionSubject

_lock = threading.Lock()
_memory: dict[str, dict] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "operational_sessions"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_path(session_id: str) -> Path:
    safe = (session_id or "default").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def load_session_payload(*, session_id: str = "default") -> dict:
    sid = (session_id or "default").strip() or "default"
    with _lock:
        cached = _memory.get(sid)
        if cached is not None:
            return dict(cached)
    path = _session_path(sid)
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                with _lock:
                    _memory[sid] = raw
                return dict(raw)
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def save_session_payload(*, session_id: str, payload: dict) -> None:
    sid = (session_id or "default").strip() or "default"
    payload = {**payload, "session_id": sid, "updated_at": datetime.now(UTC).isoformat()}
    with _lock:
        _memory[sid] = dict(payload)
    try:
        _session_path(sid).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass


def clear_operational_sessions_for_tests() -> None:
    with _lock:
        _memory.clear()


def load_subject(*, session_id: str = "default") -> SessionSubject:
    payload = load_session_payload(session_id=session_id)
    return SessionSubject.from_dict(payload.get("subject"))


def load_context(*, session_id: str = "default") -> SessionContext:
    payload = load_session_payload(session_id=session_id)
    return SessionContext.from_dict(payload.get("context"))
