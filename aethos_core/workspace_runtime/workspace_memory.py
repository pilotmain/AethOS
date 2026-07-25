# SPDX-License-Identifier: Apache-2.0
"""Workspace memory — continuity context (no hidden automation)."""

from __future__ import annotations

import json
from time import time
from typing import Any

from aethos_core.workspace_runtime.paths import workspace_runtime_root


def _path():
    return workspace_runtime_root() / "workspace_memory.json"


def _load() -> dict[str, Any]:
    path = _path()
    if not path.is_file():
        return {"active_repos": [], "preferred_workspaces": [], "recurring_commands": [], "sessions": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"active_repos": [], "preferred_workspaces": [], "recurring_commands": [], "sessions": []}


def _save(data: dict[str, Any]) -> None:
    _path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def record_workspace_context(
    *,
    workspace_id: str | None = None,
    repo_path: str | None = None,
    command: str | None = None,
    replay_id: str | None = None,
) -> None:
    data = _load()
    if workspace_id:
        preferred = list(data.get("preferred_workspaces") or [])
        entry = {"workspace_id": workspace_id, "repo_path": repo_path, "at": time()}
        preferred = [entry] + [p for p in preferred if p.get("workspace_id") != workspace_id]
        data["preferred_workspaces"] = preferred[:20]
    if command:
        cmds = list(data.get("recurring_commands") or [])
        cmds.insert(0, {"command": command[:200], "at": time(), "workspace_id": workspace_id})
        data["recurring_commands"] = cmds[:50]
    if replay_id:
        sessions = list(data.get("sessions") or [])
        sessions.insert(0, {"replay_id": replay_id, "at": time(), "workspace_id": workspace_id})
        data["sessions"] = sessions[:30]
    data["updated_at"] = time()
    _save(data)


def workspace_memory_snapshot() -> dict[str, Any]:
    return _load()


def clear_workspace_memory_for_tests() -> None:
    path = _path()
    if path.is_file():
        path.unlink()
