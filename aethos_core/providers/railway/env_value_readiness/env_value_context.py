# SPDX-License-Identifier: Apache-2.0
"""Persist Railway env value readiness state — metadata only."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_STORE: dict[str, dict[str, Any]] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "railway_env_value_readiness"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_path(session_id: str) -> Path:
    safe = (session_id or "default").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}_readiness.json"


def save_env_value_readiness(*, session_id: str, state: dict[str, Any]) -> dict[str, Any]:
    session_id = (session_id or "default").strip()
    payload = dict(state)
    payload["updated_at"] = datetime.now(UTC).isoformat()
    _STORE[session_id] = payload
    try:
        _session_path(session_id).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass
    return payload


def get_env_value_readiness(*, session_id: str, plan: dict[str, Any] | None = None) -> dict[str, Any] | None:
    session_id = (session_id or "default").strip()
    cached = _STORE.get(session_id)
    if cached is not None:
        return dict(cached)
    path = _session_path(session_id)
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and raw.get("required_env_names") is not None:
                _STORE[session_id] = raw
                return dict(raw)
        except (OSError, json.JSONDecodeError):
            pass
    return None


def record_user_marked_configured(*, session_id: str) -> None:
    session_id = (session_id or "default").strip()
    cached = get_env_value_readiness(session_id=session_id) or {}
    cached = dict(cached)
    cached["user_marked_configured_at"] = datetime.now(UTC).isoformat()
    save_env_value_readiness(session_id=session_id, state=cached)


def clear_for_tests() -> None:
    _STORE.clear()
    root = _store_dir()
    for path in root.glob("*.json"):
        path.unlink()
