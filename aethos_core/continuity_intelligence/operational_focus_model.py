# SPDX-License-Identifier: Apache-2.0
"""Current operational focus — biases vague recall toward recent investigations."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_MEMORY: dict[str, dict[str, Any]] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "continuity_intelligence"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_path(session_id: str) -> Path:
    safe = (session_id or "default").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def get_operational_focus(*, session_id: str) -> dict[str, Any]:
    session_id = (session_id or "default").strip()
    if session_id in _MEMORY:
        return dict(_MEMORY[session_id])
    path = _session_path(session_id)
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                _MEMORY[session_id] = raw
                return dict(raw)
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def update_operational_focus(
    *,
    session_id: str,
    provider: str = "",
    service: str = "",
    operation: str = "",
    execution_job_id: str = "",
    status: str = "",
    investigation: str = "",
) -> dict[str, Any]:
    session_id = (session_id or "default").strip()
    current = get_operational_focus(session_id=session_id)
    focus = {
        **current,
        "provider": provider or current.get("provider") or "",
        "service": service or current.get("service") or "",
        "operation": operation or current.get("operation") or "",
        "execution_job_id": execution_job_id or current.get("execution_job_id") or "",
        "status": status or current.get("status") or "",
        "investigation": investigation or current.get("investigation") or "",
        "updated_at": datetime.now(UTC).isoformat(),
    }
    _MEMORY[session_id] = focus
    _session_path(session_id).write_text(json.dumps(focus, indent=2), encoding="utf-8")
    return focus


def set_operational_focus(*, session_id: str, focus: dict[str, Any]) -> dict[str, Any]:
    session_id = (session_id or "default").strip()
    merged = {
        **get_operational_focus(session_id=session_id),
        **dict(focus or {}),
        "updated_at": datetime.now(UTC).isoformat(),
    }
    _MEMORY[session_id] = merged
    _session_path(session_id).write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return merged


def record_from_thread(thread: Any) -> dict[str, Any]:
    if thread is None:
        return {}
    return update_operational_focus(
        session_id=str(getattr(thread, "session_id", "") or "default"),
        provider=str(getattr(thread, "provider", "") or ""),
        service=str(getattr(thread, "service", "") or ""),
        operation=str(getattr(thread, "operation", "") or ""),
        execution_job_id=str(getattr(thread, "execution_job_id", "") or ""),
        status=str(getattr(thread, "status", "") or ""),
        investigation=str(getattr(thread, "last_system_result", "") or ""),
    )


def clear_focus_for_tests() -> None:
    _MEMORY.clear()
    root = _store_dir()
    for path in root.glob("*.json"):
        path.unlink()
