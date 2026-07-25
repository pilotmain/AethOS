# SPDX-License-Identifier: Apache-2.0
"""Operational workspace memory — active session workspace state."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_entity_runtime.lightweight_agent_registry import get_workspace, update_workspace

__all__ = ["get_workspace", "update_workspace", "snapshot_workspace"]


def snapshot_workspace(*, session_id: str = "default") -> dict[str, Any]:
    workspace = get_workspace(session_id=session_id)
    return {"session_id": session_id, "workspace": workspace, "active": bool(workspace)}
