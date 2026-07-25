# SPDX-License-Identifier: Apache-2.0
"""Persistent operator runtime state — task registry, queues, execution plans."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

_LOCK = threading.RLock()
_CACHE: dict[str, Any] | None = None


def operator_runtime_path() -> Path:
    from aethos_core.config import get_settings

    settings = get_settings()
    override = str(getattr(settings, "operator_runtime_state_path", "") or "").strip()
    if override:
        return Path(override).expanduser()
    root = Path(__file__).resolve().parents[2]
    return root / "data" / "operator_runtime.json"


def load_runtime_state(*, force: bool = False) -> dict[str, Any]:
    global _CACHE
    with _LOCK:
        if _CACHE is not None and not force:
            return _CACHE
        path = operator_runtime_path()
        if path.is_file():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    _CACHE = raw
                    return _CACHE
            except (OSError, json.JSONDecodeError):
                pass
        _CACHE = _default_state()
        return _CACHE


def save_runtime_state(st: dict[str, Any]) -> None:
    global _CACHE
    with _LOCK:
        _CACHE = st
        path = operator_runtime_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(st, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(tmp, path)


def reset_runtime_state_cache_for_tests() -> None:
    global _CACHE
    with _LOCK:
        _CACHE = None


def _default_state() -> dict[str, Any]:
    return {
        "version": 1,
        "task_registry": {},
        "execution_queue": [],
        "recovery_queue": [],
        "execution": {"plans": {}, "checkpoints": {}, "supervisor": {}},
        "orchestration": {"checkpoints": {}},
        "runtime_metrics": {},
        "sessions": {},
    }


def register_operator_session(
    *,
    session_id: str,
    channel: str = "chat",
    last_provider: str = "",
    last_subject_label: str = "",
    last_operation: str = "",
) -> dict[str, Any]:
    """Persist lightweight session registry for operator runtime parity."""
    from datetime import UTC, datetime

    sid = (session_id or "default").strip() or "default"
    st = load_runtime_state()
    sessions = st.setdefault("sessions", {})
    sessions[sid] = {
        "session_id": sid,
        "channel": channel,
        "last_provider": (last_provider or "").strip().lower(),
        "last_subject_label": (last_subject_label or "")[:240],
        "last_operation": (last_operation or "")[:120],
        "updated_at": datetime.now(UTC).isoformat(),
    }
    save_runtime_state(st)
    return dict(sessions[sid])


def operator_session_registry(*, session_id: str | None = None) -> dict[str, Any]:
    st = load_runtime_state()
    sessions = dict(st.get("sessions") or {})
    if session_id:
        row = sessions.get(session_id.strip())
        return {"ok": bool(row), "session": row}
    return {"ok": True, "count": len(sessions), "sessions": sessions}
