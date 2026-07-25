# SPDX-License-Identifier: Apache-2.0
"""Agent progression memory — evolving operational actor state."""

from __future__ import annotations

import json
import re
from pathlib import Path
from time import time
from typing import Any


def _root() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "conversation" / "operational_progression"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(session_id: str) -> Path:
    safe = re.sub(r"[^\w\-]", "_", session_id)[:120]
    return _root() / f"progression_{safe}.json"


def _load(session_id: str) -> dict[str, Any]:
    path = _path(session_id)
    if not path.is_file():
        return {"stage": 0, "agents": {}, "interaction_count": 0, "artifacts": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"stage": 0, "agents": {}, "interaction_count": 0, "artifacts": []}


def _save(session_id: str, data: dict[str, Any]) -> None:
    data["updated_at"] = time()
    _path(session_id).write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_progression_state(*, session_id: str = "default") -> dict[str, Any]:
    data = _load(session_id)
    return {
        "stage": int(data.get("stage") or 0),
        "agents": dict(data.get("agents") or {}),
        "interaction_count": int(data.get("interaction_count") or 0),
        "artifacts": list(data.get("artifacts") or []),
        "updated_at": data.get("updated_at"),
    }


def seed_progression(*, session_id: str = "default", agent_names: list[str]) -> dict[str, Any]:
    data = _load(session_id)
    agents = {name: {"status": "analyzing", "last_output_at": time()} for name in agent_names}
    data["stage"] = max(int(data.get("stage") or 0), 1)
    data["agents"] = agents
    data["seeded_at"] = time()
    _save(session_id, data)
    return get_progression_state(session_id=session_id)


def advance_progression(
    *,
    session_id: str = "default",
    agent_name: str | None = None,
    increment: int = 1,
) -> dict[str, Any]:
    data = _load(session_id)
    stage = min(int(data.get("stage") or 0) + increment, 3)
    data["stage"] = stage
    data["interaction_count"] = int(data.get("interaction_count") or 0) + 1
    agents = dict(data.get("agents") or {})
    if agent_name:
        row = dict(agents.get(agent_name) or {})
        row["status"] = "reporting" if stage >= 2 else "analyzing"
        row["last_output_at"] = time()
        agents[agent_name] = row
        data["agents"] = agents
    _save(session_id, data)
    return get_progression_state(session_id=session_id)


def record_progression_artifact(
    *,
    session_id: str = "default",
    agent_name: str,
    artifact_type: str,
    summary: str,
) -> dict[str, Any]:
    data = _load(session_id)
    artifacts: list[dict[str, Any]] = list(data.get("artifacts") or [])
    row = {
        "agent_name": agent_name,
        "artifact_type": artifact_type,
        "summary": summary[:500],
        "stage": int(data.get("stage") or 0),
        "at": time(),
    }
    artifacts.insert(0, row)
    data["artifacts"] = artifacts[:20]
    _save(session_id, data)
    return row


def clear_progression_for_tests() -> None:
    for p in _root().glob("*.json"):
        p.unlink()
