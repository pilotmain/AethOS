# SPDX-License-Identifier: Apache-2.0
"""Subagent spawn — bounded coordination under parent session."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from aethos_core.agents.runtime.registry import list_agents


def agent_list_payload() -> dict[str, Any]:
    """On-demand spawn policy — no standing specialist roster."""
    return {
        "ok": True,
        "agent_count": 0,
        "agents": list_agents(),
        "spawn_policy": {
            "execution_enabled": False,
            "mutation_execution_enabled": False,
            "max_agents_per_spawn": 5,
            "on_demand_only": True,
            "note": "Agents spawn on demand from chat or agent_spawn — no fixed roster.",
        },
    }


def spawn_role_agents_from_request(
    *,
    user_text: str,
    session_id: str,
    roles: list[str] | None = None,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """Spawn one subagent session per requested role (visible on the orchestration board)."""
    from aethos_core.agents.runtime.role_planning import (
        attach_skills_requested,
        derive_creation_objective,
        plan_role_spawns,
        resolve_role_spec,
    )
    from aethos_core.agents.runtime.role_inference import extract_requested_roles
    from aethos_core.agents.runtime.registry import build_agent_spec
    from aethos_core.agents.runtime.subagent_session_store import (
        append_subagent_message,
        create_subagent_session,
    )

    role_names = roles or extract_requested_roles(user_text)
    objective = derive_creation_objective(user_text)
    want_skills = attach_skills_requested(user_text)
    plans = plan_role_spawns(user_text) if roles is None else []
    if roles is not None:
        plans = []
        for role in role_names:
            display, capability, skills = resolve_role_spec(role, attach_skills=want_skills)
            goal = f"{display}: {objective}" if objective else f"On-demand {display} agent — ready for assigned work."
            plans.append({"role_label": display, "capability": capability, "skills": skills, "goal": goal})

    spawned: list[dict[str, Any]] = []
    for plan in plans:
        display = str(plan["role_label"])
        capability = str(plan["capability"])
        skills = list(plan.get("skills") or [])
        goal = str(plan["goal"])
        spec = build_agent_spec(capability, skills=skills, task_scoped=True)
        attached = list(spec.skills) or skills
        spawn_id = f"role-{uuid4().hex[:10]}"
        transcript = [
            {
                "step": 1,
                "agent_id": spec.agent_id,
                "capability": capability,
                "role_label": display,
                "attached_skills": attached,
                "task": goal,
                "action": "role_spawn",
                "status": "spawned",
                "summary": (
                    f"{display} spawned with skills: {', '.join(attached[:5])}."
                    if attached
                    else f"{display} spawned and ready."
                ),
            }
        ]
        row = create_subagent_session(
            parent_session_id=session_id,
            goal=goal,
            spawn_id=spawn_id,
            role_label=display,
            capability=capability,
            attached_skills=attached,
            tenant_id=tenant_id,
            initial_transcript=transcript,
            spawn_status="spawned",
        )
        if attached:
            append_subagent_message(
                str(row.get("session_key") or ""),
                role="assistant",
                content=f"Skills attached — {display}: {', '.join(attached[:6])}",
                source_tool="agent_creation",
            )
        spawned.append(
            {
                "name": display,
                "role": display,
                "capability": capability,
                "skills": attached,
                "session_key": row.get("session_key"),
                "spawn_id": row.get("spawn_id"),
                "goal": goal,
            }
        )

    return {
        "ok": True,
        "objective": objective,
        "count": len(spawned),
        "agents": spawned,
        "skills_attached": want_skills,
    }


def agent_sessions_list_payload(*, parent_session_id: str = "default", limit: int = 30) -> dict[str, Any]:
    """List persisted subagent sessions."""
    from aethos_core.agents.runtime.subagent_session_store import list_subagent_sessions

    rows = list_subagent_sessions(parent_session_id=parent_session_id, limit=limit)
    return {
        "ok": True,
        "parent_session_id": parent_session_id,
        "session_count": len(rows),
        "sessions": [
            {
                "session_key": r.get("session_key"),
                "spawn_id": r.get("spawn_id"),
                "goal": (r.get("goal") or "")[:240],
                "status": r.get("status"),
                "run_count": r.get("run_count"),
                "updated_at": r.get("updated_at"),
                "plan_id": r.get("plan_id"),
            }
            for r in rows
        ],
    }


def spawn_subagent_coordination(
    *,
    goal: str,
    session_id: str = "default",
    workspace_hint: str | None = None,
    parent_spawn_id: str | None = None,
) -> dict[str, Any]:
    """
    Run governed multi-agent coordination (subagent sessions spawn).
    Specialists execute sequentially; prior agent outputs feed the next via prior_results.
    """
    raw_goal = (goal or "").strip()
    if len(raw_goal) < 8:
        return {"ok": False, "error": "goal_too_short", "hint": "Describe the investigation or task in one sentence."}

    from aethos_core.agents.runtime.subagent_session_store import (
        create_subagent_session,
        record_subagent_run,
    )

    spawn_id = parent_spawn_id or f"spawn-{uuid4().hex[:12]}"
    session_row = create_subagent_session(
        parent_session_id=session_id,
        goal=raw_goal,
        workspace_hint=workspace_hint,
        spawn_id=spawn_id,
    )
    session_key = str(session_row.get("session_key") or "")

    outcome = _run_coordination(raw_goal, session_id=session_id, workspace_hint=workspace_hint)
    if not outcome.get("ok"):
        return {
            "ok": False,
            "spawn_id": spawn_id,
            "session_key": session_key,
            "error": outcome.get("error") or "coordination_failed",
            "read_only": True,
        }

    transcript = _build_agent_transcript(list(outcome.get("results") or []))
    record_subagent_run(session_key, outcome=outcome, goal_snapshot=raw_goal, transcript=transcript)
    # §8 — record which skills each spawned agent was given, visible in chat + board.
    skills_msg = _skills_attached_message(transcript)
    if skills_msg:
        from aethos_core.agents.runtime.subagent_session_store import append_subagent_message

        append_subagent_message(session_key, role="assistant", content=skills_msg, source_tool="agent_spawn")
    payload = _spawn_result_payload(
        spawn_id=spawn_id,
        session_key=session_key,
        goal=raw_goal,
        outcome=outcome,
        transcript=transcript,
    )
    payload["skills_attached"] = [
        {"agent_id": s.get("agent_id"), "attached_skills": s.get("attached_skills") or []} for s in transcript
    ]
    payload["run_count"] = 1
    try:  # §3 unified audit ledger — record the agent spawn (best-effort).
        from aethos_core.observability.audit_ledger import record_audit_event

        record_audit_event(
            action="agent.spawn",
            target=spawn_id,
            ref=session_key,
            metadata={"goal": raw_goal[:240], "session_id": session_id},
        )
    except Exception:  # noqa: BLE001
        pass
    return payload


def send_subagent_message(
    *,
    message: str,
    session_id: str = "default",
    session_key: str | None = None,
    spawn_id: str | None = None,
) -> dict[str, Any]:
    """Follow-up on a persisted subagent session."""
    raw_message = (message or "").strip()
    if len(raw_message) < 4:
        return {"ok": False, "error": "message_too_short"}

    from aethos_core.agents.runtime.subagent_session_store import (
        append_subagent_message,
        get_subagent_session,
        get_subagent_session_by_spawn_id,
        record_subagent_run,
    )

    row = None
    if session_key:
        row = get_subagent_session(session_key)
    elif spawn_id:
        row = get_subagent_session_by_spawn_id(spawn_id, parent_session_id=session_id)
    if row is None:
        return {
            "ok": False,
            "error": "subagent_session_not_found",
            "hint": "Use agent_sessions_list or spawn with agent_spawn first.",
        }

    key = str(row.get("session_key") or "")
    append_subagent_message(key, role="user", content=raw_message, source_tool="agent_send")

    prior_goal = str(row.get("goal") or "")
    workspace_hint = row.get("workspace_hint")
    run_num = int(row.get("run_count") or 0) + 1
    augmented_goal = (
        f"{prior_goal}\n\n"
        f"--- Follow-up ({run_num}) via agent_send ---\n"
        f"{raw_message}\n\n"
        f"Prior run plan_id: {row.get('plan_id') or 'none'}. "
        "Incorporate prior evidence; focus on the follow-up question."
    )

    outcome = _run_coordination(augmented_goal, session_id=session_id, workspace_hint=workspace_hint)
    if not outcome.get("ok"):
        return {
            "ok": False,
            "session_key": key,
            "error": outcome.get("error") or "coordination_failed",
        }

    transcript = _build_agent_transcript(list(outcome.get("results") or []))
    record_subagent_run(session_key=key, outcome=outcome, goal_snapshot=augmented_goal, transcript=transcript)
    payload = _spawn_result_payload(
        spawn_id=str(row.get("spawn_id") or ""),
        session_key=key,
        goal=augmented_goal,
        outcome=outcome,
        transcript=transcript,
    )
    payload["follow_up"] = True
    payload["message"] = raw_message
    payload["run_count"] = run_num
    return payload


def spawn_llm_developer_subagent(
    *,
    goal: str,
    session_id: str = "default",
    workspace_hint: str | None = None,
) -> dict[str, Any]:
    """Spawn a subagent session backed by the governed LLM tool loop (developer focus)."""
    from uuid import uuid4

    from aethos_core.agents.runtime.subagent_session_store import create_subagent_session, record_subagent_run
    from aethos_core.execution_brain.agent_runtime import run_agent_runtime_turn

    raw_goal = (goal or "").strip()
    spawn_id = f"llmdev-{uuid4().hex[:10]}"
    session_row = create_subagent_session(
        parent_session_id=session_id,
        goal=f"[LLM developer] {raw_goal}",
        workspace_hint=workspace_hint,
        spawn_id=spawn_id,
    )
    session_key = str(session_row.get("session_key") or "")

    runtime = run_agent_runtime_turn(raw_goal, session_id=session_id, channel="subagent")
    if runtime is None:
        return {
            "ok": False,
            "session_key": session_key,
            "spawn_id": spawn_id,
            "error": "agent_runtime_unavailable",
            "hint": "Enable AGENT_RUNTIME_ENABLED and configure a provider.",
        }

    reply = runtime.reply or ""
    outcome = {
        "ok": True,
        "merged": {"status": "llm_developer_complete"},
        "report": reply,
        "results": [
            {
                "agent_id": "dev_workspace",
                "task": raw_goal,
                "action": "llm_tool_loop",
                "status": "complete",
                "summary": reply[:500],
            }
        ],
        "plan": {"plan_id": f"llmdev-{spawn_id}", "agent_count": 1},
        "graph": {"nodes": [{"id": "dev_workspace", "label": "LLM developer"}], "edges": []},
    }
    record_subagent_run(session_key, outcome=outcome, goal_snapshot=raw_goal, transcript=outcome["results"])
    return {
        "ok": True,
        "spawn_id": spawn_id,
        "session_key": session_key,
        "reply": reply,
        "tool_calls": runtime.tool_calls,
        "used_llm": runtime.used_llm,
        "provider": runtime.provider,
        "model": runtime.model,
        "read_only": True,
        "mutation_execution_enabled": False,
    }


def get_subagent_session_payload(
    *,
    session_key: str | None = None,
    spawn_id: str | None = None,
    parent_session_id: str = "default",
) -> dict[str, Any]:
    from aethos_core.agents.runtime.subagent_session_store import (
        get_subagent_session,
        get_subagent_session_by_spawn_id,
    )

    row = get_subagent_session(session_key) if session_key else get_subagent_session_by_spawn_id(spawn_id or "", parent_session_id=parent_session_id)
    if row is None:
        return {"ok": False, "error": "subagent_session_not_found"}
    return {"ok": True, "session": row}


def _run_coordination(goal: str, *, session_id: str, workspace_hint: str | None) -> dict[str, Any]:
    from aethos_core.agents.runtime.coordination import run_agent_coordination
    from aethos_core.local_workspace.session_context import resolve_operational_hint

    hint = workspace_hint or resolve_operational_hint(None, session_id=session_id)
    return run_agent_coordination(goal=goal, session_id=session_id, workspace_hint=hint)


def _spawn_result_payload(
    *,
    spawn_id: str,
    session_key: str,
    goal: str,
    outcome: dict[str, Any],
    transcript: list[dict[str, Any]],
) -> dict[str, Any]:
    plan = outcome.get("plan") or {}
    graph = outcome.get("graph") or {}
    return {
        "ok": True,
        "spawn_id": spawn_id,
        "session_key": session_key,
        "plan_id": plan.get("plan_id"),
        "goal": goal[:2000],
        "agent_count": plan.get("agent_count") or len(transcript),
        "status": (outcome.get("merged") or {}).get("status"),
        "coordination_artifact_id": outcome.get("coordination_artifact_id"),
        "summary_artifact_id": outcome.get("summary_artifact_id"),
        "report_excerpt": (outcome.get("report") or "")[:4000],
        "transcript": transcript,
        "graph": {
            "nodes": graph.get("nodes") or [],
            "edges": graph.get("edges") or [],
            "replay": graph.get("replay") or [],
        },
        "read_only": True,
        "mutation_execution_enabled": False,
        "duration_ms": outcome.get("duration_ms"),
        "mission_control_hint": "Mission Control → Orchestration",
    }


def _attached_skills_for(agent_id: str) -> list[str]:
    """§8 — the skill/capability set the orchestrator attaches to a spawned agent."""
    try:
        from aethos_core.agents.runtime.registry import get_agent

        spec = get_agent(agent_id)
        if spec is None:
            return []
        # The agent's allowed actions are the skills it is equipped with for the
        # task; explicit spec.skills (if any) take precedence.
        return list(spec.skills) or list(spec.allowed)
    except Exception:
        return []


def _build_agent_transcript(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Inter-agent message bus view — what each specialist produced for the next."""
    transcript: list[dict[str, Any]] = []
    for idx, row in enumerate(results):
        agent_id = str(row.get("agent_id") or "unknown")
        prior_refs = []
        if idx > 0:
            prior = results[idx - 1]
            prior_refs.append(
                {
                    "from_agent": prior.get("agent_id"),
                    "artifact_id": prior.get("artifact_id"),
                    "summary": (prior.get("summary") or "")[:240],
                }
            )
        transcript.append(
            {
                "step": idx + 1,
                "agent_id": agent_id,
                "capability": agent_id,
                "attached_skills": _attached_skills_for(agent_id),
                "task": row.get("task"),
                "action": row.get("action"),
                "status": row.get("status"),
                "summary": (row.get("summary") or "")[:500],
                "received_from_prior": prior_refs,
                "artifact_id": row.get("artifact_id"),
                "substrate_invoked": row.get("substrate_invoked") or [],
                "duration_ms": row.get("duration_ms"),
            }
        )
    return transcript


def _skills_attached_message(transcript: list[dict[str, Any]]) -> str:
    """§8 — a one-line, human-readable summary of which skills each agent got."""
    parts: list[str] = []
    for step in transcript:
        skills = step.get("attached_skills") or []
        if not skills:
            continue
        parts.append(f"{step.get('agent_id')}: {', '.join(skills[:5])}")
    if not parts:
        return ""
    return "Attached skills — " + " · ".join(parts)
