# SPDX-License-Identifier: Apache-2.0
"""Workspace registry — active workspace tracking."""

from __future__ import annotations

from typing import Any


def list_active_workspaces(*, limit: int = 20) -> list[dict[str, Any]]:
    from aethos_core.local_workspace.registry import list_workspaces

    return list_workspaces(limit=limit)


def resolve_workspace(workspace_id: str | None = None, hint: str | None = None) -> dict[str, Any] | None:
    from aethos_core.local_workspace.registry import find_workspace_by_hint, get_workspace

    if workspace_id:
        return get_workspace(workspace_id)
    if hint:
        return find_workspace_by_hint(hint)
    return None


def workspace_status(workspace_id: str | None = None, hint: str | None = None) -> dict[str, Any]:
    from pathlib import Path

    row = resolve_workspace(workspace_id, hint)
    if not row:
        from aethos_core.local_workspace.readonly.actions import _repo_from_hint

        try:
            path = _repo_from_hint(hint or "aethos", session_id="default")
            return {
                "ok": True,
                "workspace_id": None,
                "path": str(path),
                "registered": False,
                "exists": Path(path).is_dir(),
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
    return {
        "ok": True,
        "workspace_id": row.get("workspace_id"),
        "name": row.get("name"),
        "path": row.get("path"),
        "registered": True,
        "stack": row.get("stack"),
        "health_state": row.get("health_state"),
    }
