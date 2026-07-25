# SPDX-License-Identifier: Apache-2.0
"""Execution progress tracking — believable operational advancement."""

from __future__ import annotations

from typing import Any

from aethos_core.agent_progression_memory.progression_store import advance_progression, get_progression_state, seed_progression
from aethos_core.operational_deliverables.deliverable_templates import get_agent_deliverable
from aethos_core.operational_artifacts.artifact_store import store_finding_artifact


def initialize_execution_progress(*, session_id: str, agent_names: list[str]) -> dict[str, Any]:
    return seed_progression(session_id=session_id, agent_names=agent_names)


def advance_execution_progress(
    *,
    session_id: str = "default",
    agent_name: str | None = None,
) -> dict[str, Any]:
    state = advance_progression(session_id=session_id, agent_name=agent_name, increment=1)
    stage = int(state.get("stage") or 1)
    if agent_name:
        deliverable = get_agent_deliverable(agent_name=agent_name, stage=stage)
        store_finding_artifact(
            session_id=session_id,
            agent_name=deliverable["agent_name"],
            summary=deliverable["headline"],
            artifact_type="progression_output",
        )
    return state


def get_execution_progress(*, session_id: str = "default") -> dict[str, Any]:
    state = get_progression_state(session_id=session_id)
    stage = int(state.get("stage") or 0)
    return {
        **state,
        "progression_active": stage > 0,
        "progression_stage": stage,
        "summary": f"Operational progression stage {stage}." if stage else "No progression started.",
    }
