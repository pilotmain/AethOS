# SPDX-License-Identifier: Apache-2.0
"""Task coordination memory — bounded, no hidden persistence."""

from __future__ import annotations

import json
from time import time
from typing import Any

from aethos_core.agents.runtime.paths import agent_artifacts_root

_MEMORY_FILE = "coordination_memory.json"


def _path():
    return agent_artifacts_root() / _MEMORY_FILE


def _load() -> dict[str, Any]:
    path = _path()
    if not path.is_file():
        return {"coordination_events": [], "task_memory": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"coordination_events": [], "task_memory": {}}


def _save(data: dict[str, Any]) -> None:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def record_coordination(
    *,
    plan_id: str,
    goal: str,
    status: str,
    artifact_id: str | None = None,
) -> None:
    data = _load()
    row = {
        "at": time(),
        "plan_id": plan_id,
        "goal": goal[:240],
        "status": status,
        "artifact_id": artifact_id,
    }
    events = list(data.get("coordination_events") or [])
    events.insert(0, row)
    data["coordination_events"] = events[:100]
    tasks = dict(data.get("task_memory") or {})
    tasks[plan_id] = {"goal": goal[:240], "status": status, "last_seen_at": time(), "artifact_id": artifact_id}
    data["task_memory"] = tasks
    data["updated_at"] = time()
    _save(data)


def get_coordination_memory() -> dict[str, Any]:
    return _load()


def clear_coordination_memory_for_tests() -> None:
    path = _path()
    if path.is_file():
        path.unlink()
