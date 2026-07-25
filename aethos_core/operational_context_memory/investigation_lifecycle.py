# SPDX-License-Identifier: Apache-2.0
"""Investigation lifecycle — snapshots and thread lifecycle management."""

from __future__ import annotations

import json
from pathlib import Path
from time import time
from typing import Any


def _root() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "conversation" / "investigation_threads"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(session_id: str) -> Path:
    return _root() / f"threads_{session_id}.json"


def load_investigation_threads(*, session_id: str = "default") -> list[dict[str, Any]]:
    path = _path(session_id)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def snapshot_investigation(
    *,
    session_id: str = "default",
    investigation: str,
    status: str = "active",
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    threads = load_investigation_threads(session_id=session_id)
    now = time()
    entry = {
        "investigation": investigation,
        "status": status,
        "snapshot_at": now,
        "context": context or {},
    }
    updated = False
    for t in threads:
        if t.get("investigation") == investigation:
            t.update(entry)
            updated = True
            break
    if not updated:
        threads.insert(0, entry)
    threads = threads[:12]
    _path(session_id).write_text(json.dumps(threads, indent=2), encoding="utf-8")
    return entry


def assess_investigation_lifecycle(*, session_id: str = "default") -> dict[str, Any]:
    threads = load_investigation_threads(session_id=session_id)
    active = [t for t in threads if t.get("status") == "active"]
    now = time()
    aged: list[dict[str, Any]] = []
    for t in active:
        age_hours = (now - float(t.get("snapshot_at") or now)) / 3600.0
        aged.append({**t, "age_hours": round(age_hours, 2)})
    return {
        "thread_count": len(threads),
        "active_count": len(active),
        "active_threads": aged[:6],
        "lifecycle_managed": True,
        "summary": f"Investigation lifecycle tracking {len(active)} active thread(s).",
    }
