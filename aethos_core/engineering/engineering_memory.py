# SPDX-License-Identifier: Apache-2.0
"""Engineering memory — patch outcomes and patterns (no mutation bypass)."""

from __future__ import annotations

import json
from pathlib import Path
from time import time
from typing import Any

from aethos_core.agents.runtime.paths import agent_artifacts_root


def _path() -> Path:
    return agent_artifacts_root() / "engineering_memory.json"


def record_engineering_outcome(
    *,
    preflight_id: str,
    execution_id: str | None,
    status: str,
    validation_status: str | None = None,
    task_kind: str | None = None,
) -> None:
    data = _load()
    events = list(data.get("events") or [])
    events.insert(
        0,
        {
            "at": time(),
            "preflight_id": preflight_id,
            "execution_id": execution_id,
            "status": status,
            "validation_status": validation_status,
            "task_kind": task_kind,
        },
    )
    data["events"] = events[:500]
    data["updated_at"] = time()
    _save(data)


def engineering_memory_snapshot() -> dict[str, Any]:
    data = _load()
    events = list(data.get("events") or [])
    failures = [e for e in events if e.get("validation_status") == "validation_failed"]
    return {
        "total_events": len(events),
        "recent_failures": failures[:10],
        "rollback_frequency": sum(1 for e in events if e.get("status") == "rollback_required"),
        "events": events[:30],
    }


def _load() -> dict[str, Any]:
    path = _path()
    if not path.is_file():
        return {"events": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"events": []}


def _save(data: dict[str, Any]) -> None:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def clear_engineering_memory_for_tests() -> None:
    path = _path()
    if path.is_file():
        path.unlink()
