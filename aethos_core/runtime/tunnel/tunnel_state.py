# SPDX-License-Identifier: Apache-2.0
"""Tunnel runtime state."""

from __future__ import annotations

import json
from pathlib import Path
from time import time
from typing import Any

_STATE: dict[str, Any] = {
    "provider": None,
    "status": "stopped",
    "local_port": None,
    "public_url": None,
    "webhook_url": None,
    "telegram_webhook_status": "unknown",
    "last_started_at": None,
    "last_stopped_at": None,
    "last_error": None,
    "enabled": False,
}


def _state_path() -> Path:
    return Path("data/tunnel/tunnel_state.json")


def load_persisted_state() -> None:
    path = _state_path()
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            _STATE.update(data)
    except (OSError, json.JSONDecodeError):
        pass


def persist_state() -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_STATE, indent=2), encoding="utf-8")


def update_state(**kwargs: Any) -> dict[str, Any]:
    _STATE.update(kwargs)
    _STATE["updated_at"] = time()
    persist_state()
    return public_state()


def get_state() -> dict[str, Any]:
    return public_state()


def public_state() -> dict[str, Any]:
    """Public tunnel snapshot — never exposes auth token."""
    return {
        "provider": _STATE.get("provider"),
        "status": _STATE.get("status") or "stopped",
        "local_port": _STATE.get("local_port"),
        "public_url": _STATE.get("public_url"),
        "webhook_url": _STATE.get("webhook_url"),
        "telegram_webhook_status": _STATE.get("telegram_webhook_status") or "unknown",
        "last_started_at": _STATE.get("last_started_at"),
        "last_stopped_at": _STATE.get("last_stopped_at"),
        "last_error": _STATE.get("last_error"),
        "enabled": bool(_STATE.get("enabled")),
    }


def reset_runtime_state() -> None:
    _STATE.update(
        {
            "status": "stopped",
            "public_url": None,
            "webhook_url": None,
            "telegram_webhook_status": "unknown",
            "last_stopped_at": time(),
        }
    )
    persist_state()
