# SPDX-License-Identifier: Apache-2.0
"""Workspace evolution — active operational workspace advancement."""

from __future__ import annotations

from typing import Any

from aethos_core.agent_progression_memory.progression_store import get_progression_state
from aethos_core.operational_entity_runtime.lightweight_agent_registry import get_workspace, update_workspace


_STAGE_STATUS = {
    0: "initialized",
    1: "landscape_scan",
    2: "partial_findings",
    3: "mature_conclusions",
}


def evolve_workspace(*, session_id: str = "default") -> dict[str, Any]:
    workspace = get_workspace(session_id=session_id)
    if not workspace:
        return {"evolved": False, "workspace": {}}

    stage = int(get_progression_state(session_id=session_id).get("stage") or 0)
    status = _STAGE_STATUS.get(stage, workspace.get("status") or "active")
    artifact_ref = workspace.get("artifact_ref") or f"workspace-{session_id[:24]}-stage-{stage}"
    evolved = update_workspace(
        session_id=session_id,
        objective=str(workspace.get("objective") or ""),
        plan_steps=list(workspace.get("plan_steps") or []),
        artifact_ref=artifact_ref if stage >= 2 else workspace.get("artifact_ref"),
    )
    evolved["progression_stage"] = stage
    evolved["status"] = status
    return {"evolved": stage > 0, "workspace": evolved, "progression_stage": stage}
