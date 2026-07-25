# SPDX-License-Identifier: Apache-2.0
"""Job artifact bridge — job outputs into progression memory."""

from __future__ import annotations

from typing import Any

from aethos_core.agent_progression_memory.progression_store import advance_progression
from aethos_core.execution_progress_tracking.progress_tracker import advance_execution_progress
from aethos_core.investigative_continuity_memory.reasoning_chain import record_reasoning_step
from aethos_core.operational_artifacts.artifact_store import store_finding_artifact
from aethos_core.operational_deliverables.deliverable_templates import get_agent_deliverable
from aethos_core.operational_entity_runtime.lightweight_agent_registry import get_workspace, update_workspace


def _workspace_objective(session_id: str) -> str:
    ws = get_workspace(session_id=session_id)
    return str(ws.get("objective") or "On-demand agents from operator request")


def apply_job_artifact(
    *,
    session_id: str,
    job_type: str,
    entity_name: str | None,
    output: dict[str, Any],
) -> dict[str, Any]:
    agent_name = entity_name or str(output.get("agent_name") or "Operational agent")
    stage_hint = int(output.get("stage") or 2)
    if job_type == "research_scan":
        stage_hint = 2
    elif job_type == "gtm_synthesis":
        stage_hint = max(stage_hint, 2)
    deliverable = get_agent_deliverable(agent_name=agent_name, stage=stage_hint)

    summary = str(output.get("summary") or deliverable.get("headline") or "Job output recorded.")
    artifact = store_finding_artifact(
        session_id=session_id,
        agent_name=deliverable["agent_name"],
        summary=summary,
        artifact_type=f"job_{job_type}",
    )
    advance_execution_progress(session_id=session_id, agent_name=deliverable["agent_name"])
    record_reasoning_step(
        session_id=session_id,
        agent_name=deliverable["agent_name"],
        stage=stage_hint,
        hypothesis=str(deliverable.get("conclusion") or summary)[:240],
        findings=list(deliverable.get("findings") or []),
        conclusion=str(deliverable.get("conclusion") or summary),
    )
    workspace = update_workspace(
        session_id=session_id,
        objective=str(output.get("objective") or _workspace_objective(session_id)),
        plan_steps=list(output.get("plan_steps") or []),
        artifact_ref=str(artifact.get("summary") or summary)[:80],
    )
    return {
        "artifact": artifact,
        "deliverable": deliverable,
        "workspace": workspace,
        "summary": summary,
    }
