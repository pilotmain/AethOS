# SPDX-License-Identifier: Apache-2.0
"""Session-scoped active workspace for engineering operations."""

from __future__ import annotations

import json
from pathlib import Path
from time import time
from typing import Any

from aethos_core.local_workspace.paths import registry_root
from aethos_core.local_workspace.registry import find_workspace_by_hint, list_workspaces, resolve_workspace_path

_CONTEXT_FILE = "session_context.json"


def _path() -> Path:
    return registry_root() / _CONTEXT_FILE


def _load() -> dict[str, Any]:
    path = _path()
    if not path.is_file():
        return {"sessions": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"sessions": {}}


def _save(data: dict[str, Any]) -> None:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def set_active_workspace(session_id: str, workspace: dict[str, Any]) -> None:
    data = _load()
    sessions = dict(data.get("sessions") or {})
    sessions[session_id] = {
        "workspace_id": workspace.get("workspace_id"),
        "name": workspace.get("name"),
        "path": workspace.get("path"),
        "updated_at": time(),
    }
    data["sessions"] = sessions
    data["updated_at"] = time()
    _save(data)


def get_active_workspace(session_id: str) -> dict[str, Any] | None:
    sessions = (_load().get("sessions") or {})
    row = sessions.get(session_id)
    if not isinstance(row, dict):
        return None
    ws_id = row.get("workspace_id")
    if ws_id:
        from aethos_core.local_workspace.registry import get_workspace

        full = get_workspace(str(ws_id))
        if full:
            return full
    return row


def resolve_operational_hint(explicit_hint: str | None, *, session_id: str = "default", cwd: str | None = None) -> str:
    """Resolve workspace hint via deployment target resolver layered defaults."""
    from aethos_core.deployment_targets.resolver import resolve_workspace_hint_for_session

    return resolve_workspace_hint_for_session(explicit_hint, session_id=session_id, cwd=cwd)


def resolve_workspace_by_cwd_prefix(cwd: str | None = None) -> dict[str, Any] | None:
    """Longest registered workspace path that prefixes the current directory."""
    import os

    raw = (cwd or os.getcwd()).strip()
    if not raw:
        return None
    try:
        cwd_path = Path(raw).expanduser().resolve()
    except OSError:
        return None

    best: dict[str, Any] | None = None
    best_len = -1
    for row in list_workspaces():
        path_raw = str(row.get("path") or "").strip()
        if not path_raw:
            continue
        try:
            workspace_path = Path(path_raw).expanduser().resolve()
        except OSError:
            continue
        if workspace_path == cwd_path or cwd_path.is_relative_to(workspace_path):
            length = len(str(workspace_path))
            if length > best_len:
                best = row
                best_len = length
    return best


def clear_session_context_for_tests() -> None:
    path = _path()
    if path.is_file():
        path.unlink()
