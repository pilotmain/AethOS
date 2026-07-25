# SPDX-License-Identifier: Apache-2.0
"""Session context for the latest Railway deployment readiness run."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_CONTEXT_STORE: dict[str, dict[str, Any]] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "railway_deployment_readiness"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_path(session_id: str) -> Path:
    safe = (session_id or "default").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}_latest.json"


def save_readiness_context(
    *,
    session_id: str,
    checks: dict[str, Any],
    user_text: str = "",
    skip_lifecycle_sync: bool = False,
) -> None:
    session_id = (session_id or "default").strip()
    payload = {
        "checks": dict(checks),
        "user_text": user_text,
        "updated_at": datetime.now(UTC).isoformat(),
    }
    _CONTEXT_STORE[session_id] = payload
    try:
        _session_path(session_id).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass
    if not skip_lifecycle_sync:
        from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_sync import (
            sync_lifecycle_after_readiness,
        )

        sync_lifecycle_after_readiness(session_id=session_id, checks=dict(checks))


def get_readiness_context(*, session_id: str) -> dict[str, Any] | None:
    session_id = (session_id or "default").strip()
    cached = _CONTEXT_STORE.get(session_id)
    if cached is not None:
        return dict(cached)
    path = _session_path(session_id)
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and raw.get("checks"):
                _CONTEXT_STORE[session_id] = raw
                return dict(raw)
        except (OSError, json.JSONDecodeError):
            pass
    return None


def clear_for_tests() -> None:
    _CONTEXT_STORE.clear()
    root = _store_dir()
    for path in root.glob("*.json"):
        path.unlink()
