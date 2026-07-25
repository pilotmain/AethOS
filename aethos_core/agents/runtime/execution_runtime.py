# SPDX-License-Identifier: Apache-2.0
"""Execution runtime — operational entity orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.agent_continuity_memory.continuity_store import build_agent_continuity_context, record_agent_continuity
from aethos_core.agent_progression_memory.progression_store import get_progression_state, seed_progression
from aethos_core.agents.runtime.role_inference import extract_requested_roles, infer_execution_intent
from aethos_core.agents.runtime.execution_reply_shaping import (
    compose_agent_initialization_reply,
    compose_entity_status_reply,
)
from aethos_core.conversation.progression_inference import infer_progression_intent
from aethos_core.conversation.progression_compat import (
    compose_agent_conclusion_reply,
    compose_completion_watch_reply,
    compose_job_status_reply,
    compose_progress_inquiry_reply,
    compose_progression_workspace_reply,
)
from aethos_core.entity_grounding.entity_disambiguation import ground_entity_query
from aethos_core.live_operational_grounding.regression_guardrails import assess_regression_guardrails
from aethos_core.operational_entity_runtime.lightweight_agent_registry import (
    get_workspace,
    list_active_entities,
    register_operational_entity,
    update_workspace,
)
from aethos_core.operational_progression_runtime.progression_runtime import seed_operational_progression
from aethos_core.workspace_evolution.workspace_evolution import evolve_workspace


def _reconcile_progression(*, session_id: str) -> None:
    entities = list_active_entities(session_id=session_id)
    if not entities:
        return
    state = get_progression_state(session_id=session_id)
    if int(state.get("stage") or 0) < 1:
        seed_progression(session_id=session_id, agent_names=[str(e.get("name") or "") for e in entities if e.get("name")])


def _progression_result(
    *,
    reply: str,
    intent: str,
    session_id: str,
    entities: list[dict[str, Any]],
    workspace: dict[str, Any],
    user_text: str,
) -> dict[str, Any]:
    workspace_evolution = evolve_workspace(session_id=session_id)
    grounding = ground_entity_query(query=user_text, session_id=session_id)
    continuity = record_agent_continuity(session_id=session_id, entities=entities, objective=workspace.get("objective"))
    guardrails = assess_regression_guardrails(reply=reply, grounded=True)
    return {
        "reply": reply,
        "intent": intent,
        "lane": "operational_progression",
        "grounded": True,
        "entity_grounding": grounding,
        "continuity": continuity,
        "workspace_evolution": workspace_evolution,
        "regression_guardrails": guardrails,
        "execution_qualified": guardrails.get("guardrails_qualified", True),
        "summary": "Operational progression — evolving agent findings.",
    }


def orchestrate_operational_entity(
    *,
    user_text: str,
    session_id: str = "default",
    channel: str = "chat",
) -> dict[str, Any] | None:
    _reconcile_progression(session_id=session_id)
    progression_info = infer_progression_intent(user_text)
    entities = list_active_entities(session_id=session_id)
    workspace = get_workspace(session_id=session_id)

    if progression_info.get("progression_prompt"):
        intent = str(progression_info.get("intent") or "")
        target = progression_info.get("target_agent")
        if intent == "job_status":
            reply = compose_job_status_reply(session_id=session_id)
            guardrails = assess_regression_guardrails(reply=reply, grounded=True)
            return {
                "reply": reply,
                "intent": intent,
                "lane": "operational_progression",
                "grounded": True,
                "regression_guardrails": guardrails,
                "execution_qualified": guardrails.get("guardrails_qualified", True),
                "summary": "Job status honesty — durable lifecycle reply.",
            }
        if not entities:
            return None
        if intent == "agent_conclusion":
            reply = compose_agent_conclusion_reply(session_id=session_id, agent_name=target)
        elif intent == "completion_watch":
            reply = compose_completion_watch_reply(session_id=session_id)
        elif intent == "progress_inquiry":
            reply = compose_progress_inquiry_reply(session_id=session_id, agent_name=target)
        else:
            return None
        return _progression_result(
            reply=reply,
            intent=intent,
            session_id=session_id,
            entities=entities,
            workspace=workspace,
            user_text=user_text,
        )

    intent_info = infer_execution_intent(user_text)
    if not intent_info.get("execution_prompt"):
        return None

    intent = str(intent_info.get("intent") or "")
    grounding = ground_entity_query(query=user_text, session_id=session_id)

    if intent == "agent_creation":
        from aethos_core.agents.runtime.subagent_ops import spawn_role_agents_from_request
        from aethos_core.agents.runtime.role_planning import derive_creation_objective

        roles = extract_requested_roles(user_text)
        objective = derive_creation_objective(user_text)
        spawn_batch = spawn_role_agents_from_request(user_text=user_text, session_id=session_id, roles=roles)
        spawned_agents = list(spawn_batch.get("agents") or [])
        created = []
        for idx, role in enumerate(roles):
            agent = spawned_agents[idx] if idx < len(spawned_agents) else {}
            created.append(
                register_operational_entity(
                    session_id=session_id,
                    name=str(agent.get("name") or role),
                    role=str(agent.get("role") or role),
                    objective=objective or str(agent.get("goal") or ""),
                )
            )
        plan_steps = [f"{a.get('name', 'Agent')}: ready on orchestration board" for a in spawn_batch.get("agents") or []]
        workspace = update_workspace(
            session_id=session_id,
            objective=objective or "On-demand agents spawned from your request",
            plan_steps=plan_steps or ["Agents visible on the orchestration board"],
        )
        seed_operational_progression(session_id=session_id, agent_names=[r["name"] for r in created])
        reply = compose_agent_initialization_reply(
            entities=created,
            workspace=workspace,
            objective=workspace.get("objective") or "",
            spawn_batch=spawn_batch,
        )
        entities = created
    elif intent == "entity_status":
        reply = compose_entity_status_reply(entities=entities, workspace=workspace)
    elif intent == "workspace_results":
        reply = compose_progression_workspace_reply(session_id=session_id, entities=entities, workspace=workspace)
    else:
        return None

    continuity = record_agent_continuity(session_id=session_id, entities=entities, objective=workspace.get("objective"))
    guardrails = assess_regression_guardrails(reply=reply, grounded=True)

    return {
        "reply": reply,
        "intent": intent,
        "lane": "operational_entity",
        "grounded": True,
        "entity_grounding": grounding,
        "continuity": continuity,
        "regression_guardrails": guardrails,
        "execution_qualified": guardrails.get("guardrails_qualified", True),
        "summary": "Operational entity execution continuity active.",
    }


def assess_execution_presence(*, session_id: str = "default") -> dict[str, Any]:
    ctx = build_agent_continuity_context(session_id=session_id)
    from aethos_core.execution_progress_tracking.progress_tracker import get_execution_progress

    progress = get_execution_progress(session_id=session_id)
    return {
        **ctx,
        "execution_present": ctx.get("has_active_entities", False),
        "progression_active": progress.get("progression_active", False),
        "progression_stage": progress.get("progression_stage", 0),
        "summary": ctx.get("summary"),
    }
