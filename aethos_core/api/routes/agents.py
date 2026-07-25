# SPDX-License-Identifier: Apache-2.0
"""Multi-agent runtime API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["agents"])


class AgentDelegateIn(BaseModel):
    goal: str
    parent_session_id: str = "operator"
    workspace_hint: str | None = None


@router.get("/agents")
def list_agents_api() -> dict[str, Any]:
    from aethos_core.agents.memory.task_memory import get_coordination_memory
    from aethos_core.agents.runtime.artifacts import get_agent_artifact, list_agent_artifacts
    from aethos_core.agents.runtime.registry import list_agents

    # 80 (not 30) so granular evidence artifacts still surface in the Evidence
    # sub-view after a busy run pushes them down the list. Only the three summary
    # types below trigger an extra hydration read, so this stays cheap.
    artifacts = list_agent_artifacts(limit=80)
    hydrated: list[dict[str, Any]] = []
    for row in artifacts:
        item = dict(row)
        if item.get("artifact_type") in ("agent_coordination", "agent_confidence_summary", "agent_summary"):
            full = get_agent_artifact(str(item.get("artifact_id") or ""))
            if full and full.get("payload"):
                item["payload"] = full["payload"]
        hydrated.append(item)

    return {
        "ok": True,
        "agents": list_agents(),
        "artifacts": hydrated,
        "coordination_memory": get_coordination_memory(),
    }


@router.get("/agents/artifacts")
def list_agent_artifacts_api(limit: int = 40) -> dict[str, Any]:
    from aethos_core.agents.runtime.artifacts import list_agent_artifacts

    return {"ok": True, "artifacts": list_agent_artifacts(limit=limit)}


@router.get("/agents/artifacts/{artifact_id}")
def get_agent_artifact_api(artifact_id: str) -> dict[str, Any]:
    from aethos_core.agents.runtime.artifacts import get_agent_artifact

    row = get_agent_artifact(artifact_id)
    if not row:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {"ok": True, "artifact": row}


@router.get("/agents/subagent-sessions")
def list_subagent_sessions_api(
    parent_session_id: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    from aethos_core.agents.runtime.subagent_session_store import list_subagent_sessions

    parent_filter = (parent_session_id or "").strip()
    if parent_filter.lower() in {"", "all", "*"}:
        parent_filter = None
    rows = list_subagent_sessions(parent_session_id=parent_filter, limit=limit)
    return {
        "ok": True,
        "parent_session_id": parent_filter,
        "sessions": rows,
        "count": len(rows),
    }


@router.get("/agents/subagent-sessions/{session_key:path}")
def get_subagent_session_api(session_key: str) -> dict[str, Any]:
    from aethos_core.agents.runtime.subagent_session_store import get_subagent_session

    row = get_subagent_session(session_key)
    if not row:
        raise HTTPException(status_code=404, detail="Subagent session not found")
    return {"ok": True, "session": row}


@router.post("/agents/spawn")
def delegate_agent_spawn_api(body: AgentDelegateIn) -> dict[str, Any]:
    """§7 — delegate a task from the orchestration board (flag-gated, read-only)."""
    from aethos_core.config import get_settings

    if not getattr(get_settings(), "orchestration_board_delegate_enabled", False):
        return {
            "ok": False,
            "error": "delegate_disabled",
            "hint": "Set ORCHESTRATION_BOARD_DELEGATE_ENABLED=true to delegate tasks from the board.",
        }
    from aethos_core.agents.runtime.subagent_ops import spawn_subagent_coordination

    return spawn_subagent_coordination(
        goal=body.goal,
        session_id=(body.parent_session_id or "operator").strip() or "operator",
        workspace_hint=body.workspace_hint,
    )


@router.get("/agents/coordination/{plan_id}")
def get_coordination_api(plan_id: str) -> dict[str, Any]:
    from aethos_core.agents.memory.task_memory import get_coordination_memory

    memory = get_coordination_memory()
    task = (memory.get("task_memory") or {}).get(plan_id)
    if not task:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"ok": True, "plan_id": plan_id, "task": task}


class CoordinationRunIn(BaseModel):
    goal: str
    session_id: str = "agent-comms"


@router.post("/agents/coordination/run")
def run_coordination_api(body: CoordinationRunIn) -> dict[str, Any]:
    """Run a bounded read-only multi-agent coordination and return its inter-agent comms
    (for the live multi-agent visual). Never mutates."""
    if not body.goal.strip():
        raise HTTPException(status_code=422, detail="goal must not be empty")
    from aethos_core.agents.runtime.comms import get_agent_comms
    from aethos_core.agents.runtime.coordination import run_agent_coordination

    sid = (body.session_id or "agent-comms").strip() or "agent-comms"
    result = run_agent_coordination(goal=body.goal.strip(), session_id=sid)
    return {
        "ok": bool(result.get("ok", True)),
        "session_id": sid,
        "report": result.get("report"),
        "comms": get_agent_comms(sid),
    }


@router.get("/agents/comms/{session_id}")
def get_agent_comms_api(session_id: str) -> dict[str, Any]:
    """Fetch the inter-agent communication log for a session (drives the live graph)."""
    from aethos_core.agents.runtime.comms import get_agent_comms

    return {"ok": True, "comms": get_agent_comms(session_id)}


@router.post("/agents/coordination/start")
def start_coordination_api(body: CoordinationRunIn) -> dict[str, Any]:
    """Start a coordination in the BACKGROUND and return a session id immediately, so the
    live visual can poll /agents/comms/{id} and animate the team as it works — large teams
    no longer block the request (or hit a proxy timeout). Read-only; never mutates."""
    import threading
    import uuid

    if not body.goal.strip():
        raise HTTPException(status_code=422, detail="goal must not be empty")

    from aethos_core.agents.runtime.comms import finish_coordination_comms, start_coordination_comms
    from aethos_core.agents.runtime.coordination import run_agent_coordination
    from aethos_core.tenancy import get_current_tenant, tenant_scope

    sid = f"comms-{uuid.uuid4().hex[:10]}"
    goal = body.goal.strip()
    owner = get_current_tenant() or "default"
    # Seed the roster immediately so the panel can render nodes before events arrive.
    start_coordination_comms(sid, [], goal=goal, tenant_id=owner)

    def _worker() -> None:
        # Executor threads don't inherit the request tenant contextvar — re-establish it.
        with tenant_scope(owner):
            try:
                run_agent_coordination(goal=goal, session_id=sid)
            except Exception:  # noqa: BLE001
                finish_coordination_comms(sid, tenant_id=owner)

    threading.Thread(target=_worker, name=f"coord-{sid}", daemon=True).start()
    return {"ok": True, "session_id": sid, "status": "running"}
