# SPDX-License-Identifier: Apache-2.0
"""Operational entity runtime aggregate — Phase 11.7.6."""

from __future__ import annotations

from typing import Any

from aethos_core.agents.runtime.execution_runtime import assess_execution_presence, orchestrate_operational_entity


def assess_operational_entity_runtime(
    *,
    session_id: str = "default",
    channel: str = "chat",
    user_text: str = "",
) -> dict[str, Any]:
    """Phase 11.7.6 — operational entity realism & execution continuity."""
    execution = orchestrate_operational_entity(user_text=user_text, session_id=session_id, channel=channel) if user_text else None
    presence = assess_execution_presence(session_id=session_id)
    entity_qualified = bool(presence.get("has_active_entities")) or bool(execution and execution.get("execution_qualified"))
    return {
        "ok": True,
        "phase": "11.7.6",
        "converged": entity_qualified,
        "execution": execution,
        "execution_presence": presence,
        "summary": (
            "Operational entity runtime active — persistent agents and execution continuity enabled."
            if entity_qualified
            else "Operational entity runtime ready — awaiting entity initialization or workspace activation."
        ),
    }
