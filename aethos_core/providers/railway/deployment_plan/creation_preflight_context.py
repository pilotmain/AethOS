# SPDX-License-Identifier: Apache-2.0
"""Durable Railway new-service creation preflight artifacts."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_STORE: dict[str, dict[str, Any]] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "railway_deployment_creation_preflight"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_path(session_id: str) -> Path:
    safe = (session_id or "default").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}_preflight.json"


def save_creation_preflight(
    *,
    session_id: str,
    preflight: dict[str, Any],
    skip_lifecycle_sync: bool = False,
) -> None:
    session_id = (session_id or "default").strip()
    payload = dict(preflight)
    payload["updated_at"] = datetime.now(UTC).isoformat()
    if not payload.get("preflight_id"):
        payload["preflight_id"] = f"rpref-{uuid.uuid4().hex[:12]}"
    _STORE[session_id] = payload
    try:
        _session_path(session_id).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass
    if not skip_lifecycle_sync and payload.get("preflight_id"):
        from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_sync import (
            sync_lifecycle_after_preflight,
        )

        sync_lifecycle_after_preflight(session_id=session_id, preflight=payload)


def get_creation_preflight(*, session_id: str) -> dict[str, Any] | None:
    session_id = (session_id or "default").strip()
    cached = _STORE.get(session_id)
    if cached is not None:
        return dict(cached)
    path = _session_path(session_id)
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and raw.get("preflight_id"):
                _STORE[session_id] = raw
                return dict(raw)
        except (OSError, json.JSONDecodeError):
            pass
    return None


def clear_creation_preflight(*, session_id: str | None = None) -> None:
    if session_id:
        sid = session_id.strip()
        _STORE.pop(sid, None)
        try:
            _session_path(sid).unlink(missing_ok=True)
        except OSError:
            pass
        return
    _STORE.clear()


def clear_for_tests() -> None:
    clear_creation_preflight()
    root = _store_dir()
    for path in root.glob("*.json"):
        path.unlink()
