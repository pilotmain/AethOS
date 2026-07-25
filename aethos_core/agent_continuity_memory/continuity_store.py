# SPDX-License-Identifier: Apache-2.0
"""Agent continuity memory — persistent operational actor state."""

from __future__ import annotations

from time import time
from typing import Any

from aethos_core.operational_entity_runtime.lightweight_agent_registry import (
    get_workspace,
    list_active_entities,
)


def record_agent_continuity(
    *,
    session_id: str = "default",
    plan_id: str | None = None,
    entities: list[dict[str, Any]] | None = None,
    objective: str | None = None,
) -> dict[str, Any]:
    """Snapshot active agent continuity for conversational follow-ups."""
    active = entities or list_active_entities(session_id=session_id)
    workspace = get_workspace(session_id=session_id)
    return {
        "session_id": session_id,
        "active_entities": active,
        "entity_count": len(active),
        "workspace": workspace,
        "plan_id": plan_id,
        "objective": objective or workspace.get("objective"),
        "recorded_at": time(),
        "continuity_available": bool(active or workspace),
    }


def build_agent_continuity_context(*, session_id: str = "default") -> dict[str, Any]:
    active = list_active_entities(session_id=session_id)
    workspace = get_workspace(session_id=session_id)
    names = [e.get("name") for e in active if e.get("name")]
    return {
        "has_active_entities": bool(active),
        "entity_names": names,
        "workspace_objective": workspace.get("objective"),
        "workspace_status": workspace.get("status"),
        "artifact_ref": workspace.get("artifact_ref"),
        "summary": (
            f"Active operational entities: {', '.join(names)}."
            if names
            else "No active operational entities in this session."
        ),
    }
