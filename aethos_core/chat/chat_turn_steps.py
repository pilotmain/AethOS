# SPDX-License-Identifier: Apache-2.0
"""Three-step chat turn resolution — safety, operational fast path, agent runtime."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aethos_core.chat.service import ChatTurnResult


# §B1 — high-precision deterministic intent labels (observability + the gate below).
# Only the highest-confidence, previously-misrouting intents change control flow;
# the rest are labels so a turn maps to one primary capability deterministically.
_REPO_REVIEW_RX = re.compile(
    r"\b(review|audit|analy[sz]e|inspect|read|go through|walk through|explain)\b.{0,40}"
    r"\b(local\s+(?:repo|repository|workspace)|registered\s+workspace|code\s*base|codebase|source\s+code)\b",
    re.I,
)
_DEPLOY_RX = re.compile(r"\b(deploy|redeploy|ship|launch)\b", re.I)
_PROVIDER_READONLY_RX = re.compile(
    r"\b(show|list|status|health|logs?|inventory|projects?|services?)\b", re.I
)
_RESEARCH_RX = re.compile(r"\b(research|compare|look up|find out|investigate|web search)\b", re.I)
# External/web research — deliberately tight so it never claims an operational "compare the
# two failed deployments" turn. Used to stop provider-inventory / operational-cognition lanes
# from hijacking a research ask just because it mentions a provider name (e.g. "research
# Railway vs Vercel" → Vercel inventory, "research Plaid …" → killit-api recall).
_EXTERNAL_RESEARCH_RX = re.compile(
    r"^\s*research\b|\bcite\s+sources?\b|\blook\s+up\b|\b(web\s+search|search\s+the\s+web|search\s+online|find\s+online)\b",
    re.I,
)


def is_external_research_request(text: str) -> bool:
    return bool(_EXTERNAL_RESEARCH_RX.search((text or "").strip()))
_MUTATION_RX = re.compile(r"\b(restart|rollback|set\s+env|scale|delete|stop|start)\b", re.I)


def classify_primary_intent(text: str, *, session_id: str = "default") -> str:
    """Map a turn to ONE primary capability (deterministic, same input → same label).

    Returns one of: orchestration | canvas | repo_review | deploy | provider_readonly
    | research | mutation | chitchat | unknown. The Step-2 gate dispatches the
    high-confidence intents (orchestration / canvas) directly so the legacy routers
    act as handlers behind this decision rather than 28 competing matchers.
    """
    raw = (text or "").strip()
    if not raw:
        return "chitchat"
    from aethos_core.agents.runtime.planner import is_command_center_orchestration_request
    from aethos_core.chat.deterministic import is_canvas_render_request

    if is_command_center_orchestration_request(raw, session_id=session_id):
        return "orchestration"
    if is_canvas_render_request(raw):
        return "canvas"
    if _REPO_REVIEW_RX.search(raw):
        return "repo_review"
    low = raw.lower()
    if _DEPLOY_RX.search(low):
        return "deploy"
    if _MUTATION_RX.search(low):
        return "mutation"
    if _PROVIDER_READONLY_RX.search(low):
        return "provider_readonly"
    if _RESEARCH_RX.search(low):
        return "research"
    return "unknown"


def _dispatch_orchestration(raw: str, *, session_id: str) -> "ChatTurnResult | None":
    """Deterministic command-center / multi-agent orchestration dispatch (§B1).

    Mirrors the legacy Step-2 orchestration block, lifted to the top so the
    decision is made once and never lost to an earlier keyword lane.
    """
    from aethos_core.config import get_settings

    if not get_settings().agent_runtime_enabled:
        return _tuple_result(
            (
                "Multi-agent orchestration needs `AGENT_RUNTIME_ENABLED` — it's currently off.\n\n"
                "Set `AGENT_RUNTIME_ENABLED=true` and restart the runtime, and I'll spin up the "
                "agents, populate **Mission Control → Orchestration**, and coordinate them on this.",
                "agent_runtime_disabled",
                {
                    "lane": "agent_runtime_disabled",
                    "feature": "multi_agent_orchestration",
                    "agent_runtime_enabled": "false",
                },
            ),
            session_id=session_id,
        )
    if get_settings().durable_agent_jobs_enabled:
        from aethos_core.chat.agent_intelligence import multi_agent_job_reply

        handled = multi_agent_job_reply(raw, session_id=session_id)
    else:
        from aethos_core.chat.agent_intelligence import multi_agent_reply

        handled = multi_agent_reply(raw, session_id=session_id)
    if handled:
        return _tuple_result(handled, session_id=session_id)
    return None


def _save_trace(session_id: str, meta: dict, intent: str) -> None:
    from aethos_core.chat.route_trace import save_last_route_trace

    save_last_route_trace(session_id=session_id, meta=meta, intent=intent)


def _tuple_result(
    handled: tuple[str, str, dict[str, str]],
    *,
    session_id: str,
    used_llm: bool = False,
) -> "ChatTurnResult":
    from aethos_core.chat.service import ChatTurnResult

    body, intent, meta = handled
    _save_trace(session_id, meta, intent)
    return ChatTurnResult(
        reply=body,
        intent=intent,
        provider_stream=False,
        used_llm=used_llm,
        meta=meta,
    )


def try_safety_short_circuit_turn(
    raw: str,
    *,
    session_id: str,
    channel: str = "chat",
    surface: str = "webchat",
) -> "ChatTurnResult | None":
    """Step 1 — retry, task frame, approval continuations (before operational kernel).

    Accepts ``channel``/``surface`` inbound metadata (handoff §1/§6/§11). The DM
    pairing/allowlist gate for untrusted channels attaches here in a later step.
    """
    from aethos_core.task_frame.retry_active_operation import compose_retry_active_operation_reply

    retry_result = compose_retry_active_operation_reply(raw, session_id=session_id)
    if retry_result is not None:
        return _tuple_result(retry_result, session_id=session_id)

    from aethos_core.chat.safety_continuation import is_follow_up_turn, is_meta_complaint_turn
    from aethos_core.task_frame.task_continuation import compose_task_continuation_reply

    if not (is_meta_complaint_turn(raw) or is_follow_up_turn(raw, session_id=session_id)):
        task_continuation = compose_task_continuation_reply(raw, session_id=session_id)
        if task_continuation is not None:
            return _tuple_result(task_continuation, session_id=session_id)

    return None


def try_operational_fast_path_turn(
    raw: str,
    *,
    session_id: str,
    channel: str,
    emotional_context: dict[str, object] | None,
    surface: str = "webchat",
) -> "ChatTurnResult | None":
    """Step 2 — kernel, FIX/MC gates, provider flows, intelligence lanes (legacy)."""
    # §2 — soul / identity questions answer warmly from SOUL.md, before any
    # deflecting relational/generic lane can claim them. Operational prompts are
    # excluded so "restart the service" style asks still route normally.
    from aethos_core.aethos_identity.self_consistency_guard import is_operational_prompt
    from aethos_core.continuity_intelligence.conversational_identity_runtime import (
        compose_conversational_identity_reply,
        is_identity_soul_prompt,
    )

    if is_identity_soul_prompt(raw) and not is_operational_prompt(raw):
        soul_reply = compose_conversational_identity_reply(raw, session_id=session_id)
        if soul_reply is not None:
            return _tuple_result(soul_reply, session_id=session_id)

    from aethos_core.runtime.runtime_config_intent import is_runtime_provider_config_question
    from aethos_core.runtime_truth_alignment.runtime_truth_alignment_router import route_runtime_truth_alignment

    if is_runtime_provider_config_question(raw):
        routed = route_runtime_truth_alignment(raw, session_id=session_id)
        if routed is not None:
            return _tuple_result(routed, session_id=session_id)
        from aethos_core.chat.handlers import model_config_reply

        return _tuple_result(
            (model_config_reply(), "runtime_config_query", {"lane": "runtime_config_query"}),
            session_id=session_id,
        )

    # §A1 — one deterministic gate before the legacy router scramble.
    from aethos_core.chat.chat_intent_gate import classify_chat_turn_gate, gate_blocks_operational_scramble
    from aethos_core.chat.conversational_turn_resolver import try_conversational_turn

    gate = classify_chat_turn_gate(raw, session_id=session_id)
    if gate_blocks_operational_scramble(gate):
        conv = try_conversational_turn(raw, session_id=session_id, channel=channel, gate=gate)
        if conv is not None:
            _save_trace(session_id, conv.meta or {}, conv.intent)
            return conv
        return None

    if gate.command_kind == "canvas":
        return None

    from aethos_core.agents.runtime.planner import (
        is_multi_agent_request,
    )
    from aethos_core.chat.agent_intelligence import multi_agent_reply
    from aethos_core.chat.subagent_session_lane import subagent_session_reply
    from aethos_core.config import get_settings
    from aethos_core.execution_brain.agent_provider_cloud import is_agent_provider_cloud_request

    # §B1 — deterministic intent gate. Classify the turn once into one primary
    # capability so the legacy routers act as handlers behind the decision rather
    # than 28 competing matchers. Conservative + additive: only the high-confidence,
    # previously-misrouting intents are steered here; everything else flows through
    # the unchanged chain.
    primary_intent = classify_primary_intent(raw, session_id=session_id)

    # Canvas render commands belong in Step 3 (agent runtime → canvas_render).
    # Skip Step 2 so informational/help routers cannot steal the turn.
    if primary_intent == "canvas":
        return None

    # An explicit command-center / orchestration ask is dispatched first so it can
    # never be claimed by an earlier keyword lane or the world-model follow-up router.
    if primary_intent == "orchestration":
        orchestration = _dispatch_orchestration(raw, session_id=session_id)
        if orchestration is not None:
            return orchestration

    from aethos_core.chat.llm_developer_subagent_lane import llm_developer_subagent_reply

    llm_dev = llm_developer_subagent_reply(raw, session_id=session_id)
    if llm_dev:
        body, intent, meta = llm_dev
        used = meta.get("llm_developer_mode") == "spawn"
        return _tuple_result((body, intent, meta), session_id=session_id, used_llm=used)

    subagent_handled = subagent_session_reply(raw, session_id=session_id)
    if subagent_handled:
        return _tuple_result(subagent_handled, session_id=session_id)

    # A canvas-render ask belongs to the Step-3 agent runtime (deterministic
    # _ensure_canvas_render). Skip the comparison-HTML lane so it can't steal a
    # "render … to the canvas" turn with its "visual/html" keywords.
    if primary_intent != "canvas":
        from aethos_core.chat.comparison_html_lane import comparison_html_reply

        html_handled = comparison_html_reply(raw, session_id=session_id)
        if html_handled:
            return _tuple_result(html_handled, session_id=session_id)

    if is_multi_agent_request(raw, session_id=session_id):
        # Durable by default: run the multi-agent coordination as a server-side
        # job so the work survives navigation / tab close (the request returns a
        # job_id immediately and the UI subscribes to its lifecycle). When the
        # flag is off, fall back to the legacy in-request coordination.
        if get_settings().durable_agent_jobs_enabled:
            from aethos_core.chat.agent_intelligence import multi_agent_job_reply

            handled = multi_agent_job_reply(raw, session_id=session_id)
        else:
            handled = multi_agent_reply(raw, session_id=session_id)
        if handled:
            return _tuple_result(handled, session_id=session_id)

    if get_settings().agent_runtime_enabled and is_agent_provider_cloud_request(raw, session_id=session_id):
        return None

    from aethos_core.chat.service import ChatTurnResult, _handled_to_result
    from aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context import (
        enforce_workflow_discovery_absolute_lane_turn,
    )

    from aethos_core.post_mutation_verification.verification_intent_router import (
        continue_pending_verification_with_target,
    )

    verification_continuation = continue_pending_verification_with_target(raw, session_id=session_id)
    if verification_continuation is not None:
        return _tuple_result(verification_continuation, session_id=session_id)

    from aethos_core.chat.job_result_followup_router import compose_job_result_followup_reply

    job_result_followup = compose_job_result_followup_reply(raw, session_id=session_id)
    if job_result_followup is not None:
        return _tuple_result(job_result_followup, session_id=session_id)

    from aethos_core.task_frame.railway_redeploy_continuation import compose_railway_redeploy_continuation_reply

    railway_redeploy = compose_railway_redeploy_continuation_reply(raw, session_id=session_id)
    if railway_redeploy is not None:
        return _tuple_result(railway_redeploy, session_id=session_id)

    from aethos_core.provider_e2e_readiness.readiness_router import route_provider_e2e_readiness

    provider_readiness = route_provider_e2e_readiness(raw, session_id=session_id)
    if provider_readiness is not None:
        return _tuple_result(provider_readiness, session_id=session_id)

    from aethos_core.credentials.credential_guidance import route_provisioning_orchestration

    provisioning = route_provisioning_orchestration(raw, session_id=session_id)
    if provisioning is not None:
        return _tuple_result(provisioning, session_id=session_id)

    from aethos_core.providers.railway.greenfield_deployment.greenfield_router import (
        route_railway_greenfield_deployment_flow,
    )

    greenfield = route_railway_greenfield_deployment_flow(raw, session_id=session_id)
    if greenfield is not None:
        return _tuple_result(greenfield, session_id=session_id)

    from aethos_core.providers.vercel.greenfield_deployment.greenfield_router import (
        route_vercel_greenfield_deployment_flow,
    )

    vercel_greenfield = route_vercel_greenfield_deployment_flow(raw, session_id=session_id)
    if vercel_greenfield is not None:
        return _tuple_result(vercel_greenfield, session_id=session_id)

    from aethos_core.provider_e2e_orchestration.env_completion.supabase_routing import route_supabase_env_completion

    supabase_completion = route_supabase_env_completion(raw, session_id=session_id)
    if supabase_completion is not None:
        return _tuple_result(supabase_completion, session_id=session_id)

    from aethos_core.providers.railway.greenfield_deployment.deployment_status_followup_router import (
        route_railway_deployment_status_followup,
    )

    deployment_status = route_railway_deployment_status_followup(raw, session_id=session_id)
    if deployment_status is not None:
        return _tuple_result(deployment_status, session_id=session_id)

    from aethos_core.jobs.pending_job_approval_resolution import route_short_approval_turn

    short_approval = route_short_approval_turn(raw, session_id=session_id)
    if short_approval is not None:
        return _tuple_result(short_approval, session_id=session_id)

    from aethos_core.provider_e2e_execution.provider_e2e_execution_service import route_provider_e2e_execution

    provider_e2e = route_provider_e2e_execution(raw, session_id=session_id)
    if provider_e2e is not None:
        return _tuple_result(provider_e2e, session_id=session_id)

    from aethos_core.execution_brain.execution_brain_router import route_execution_brain_turn

    execution_brain = route_execution_brain_turn(raw, session_id=session_id)
    if execution_brain is not None:
        body, intent, meta = execution_brain
        _save_trace(session_id, meta, intent)
        return ChatTurnResult(
            reply=body,
            intent=intent,
            provider_stream=False,
            used_llm=meta.get("brain_used_llm") == "true",
            meta=meta,
        )

    result = _try_extended_operational_routers(raw, session_id=session_id, channel=channel, emotional_context=emotional_context)
    if result is not None:
        return result

    from aethos_core.operational_session.kernel_router import route_operational_conversation_kernel_turn

    operational_kernel = route_operational_conversation_kernel_turn(raw, session_id=session_id, channel=channel)
    if operational_kernel is not None:
        _save_trace(session_id, operational_kernel.meta or {}, operational_kernel.intent)
        return operational_kernel

    absolute = enforce_workflow_discovery_absolute_lane_turn(raw, session_id=session_id)
    if absolute is not None:
        return absolute

    from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
        route_workflow_discovery_hard_preemption_turn,
    )

    hard_workflow = route_workflow_discovery_hard_preemption_turn(raw, session_id=session_id)
    if hard_workflow is not None:
        return hard_workflow

    from aethos_core.chat.cognition_exception_boundary import safe_resolve_operational_turn

    operational = safe_resolve_operational_turn(
        raw,
        session_id=session_id,
        channel=channel,
        emotional_context=emotional_context,
    )
    if operational is not None:
        return operational

    from aethos_core.chat.provider_deploy_capability_intent import route_provider_deploy_capability_reply

    provider_deploy = route_provider_deploy_capability_reply(raw, session_id=session_id)
    if provider_deploy is not None:
        return _tuple_result(provider_deploy, session_id=session_id)

    from aethos_core.world_model.investigation_strategy_router import route_investigation_strategy_question

    strategy = route_investigation_strategy_question(raw, session_id=session_id)
    if strategy is not None:
        return strategy

    from aethos_core.post_mutation_verification.global_verification_preemption import (
        route_global_verification_query,
    )

    global_verification = route_global_verification_query(raw, session_id=session_id)
    if global_verification is not None:
        return global_verification

    from aethos_core.continuity_intelligence.conversational_identity_runtime import compose_conversational_identity_reply

    identity_reply = compose_conversational_identity_reply(raw, session_id=session_id)
    if identity_reply is not None:
        return _handled_to_result(identity_reply)

    from aethos_core.config import get_settings

    if not get_settings().agent_runtime_enabled:
        from aethos_core.chat.generative_knowledge_router import route_generative_knowledge_turn

        generative_knowledge = route_generative_knowledge_turn(raw, session_id=session_id, channel=channel)
        if generative_knowledge is not None:
            return generative_knowledge

    from aethos_core.chat.web_intelligence import execute_web_intelligence, is_web_intelligence_request

    if is_web_intelligence_request(raw):
        web = execute_web_intelligence(raw, session_id=session_id, channel=channel)
        if web is not None:
            return _handled_to_result(web)

    from aethos_core.chat.presence_intelligence import execute_presence_intelligence, is_presence_intelligence_request

    if is_presence_intelligence_request(raw):
        presence = execute_presence_intelligence(raw, session_id=session_id, channel=channel)
        if presence is not None:
            return _handled_to_result(presence)

    from aethos_core.chat.relational_intelligence import execute_relational_intelligence, is_relational_intelligence_request

    if is_relational_intelligence_request(raw):
        relational = execute_relational_intelligence(raw, session_id=session_id, channel=channel)
        if relational is not None:
            return _handled_to_result(relational)

    from aethos_core.chat.living_intelligence import execute_living_intelligence, is_living_intelligence_request

    if is_living_intelligence_request(raw):
        living = execute_living_intelligence(raw, session_id=session_id, channel=channel)
        if living is not None:
            return _handled_to_result(living)

    from aethos_core.channels.channel_registry import compose_channel_health_reply, is_channel_health_request

    if is_channel_health_request(raw):
        channel_health = compose_channel_health_reply(raw)
        if channel_health is not None:
            return _handled_to_result(channel_health)

    from aethos_core.chat.engineering_intelligence import execute_engineering_intent, is_engineering_intelligence_request

    if is_engineering_intelligence_request(raw):
        handled = execute_engineering_intent(raw, session_id=session_id)
        if handled:
            return _handled_to_result(handled)

    from aethos_core.conversation.entity_compat import try_operational_entity_reply

    entity = try_operational_entity_reply(raw, session_id=session_id, channel=channel)
    if entity is not None:
        body, intent, meta = entity
        return ChatTurnResult(
            reply=body,
            intent=intent,
            provider_stream=False,
            used_llm=False,
            meta=meta,
        )

    from aethos_core.chat.service import resolve_deterministic_turn

    det = resolve_deterministic_turn(raw, session_id=session_id)
    if det is not None:
        return det

    from aethos_core.conversation.polish_compat import try_grounded_chat_reply

    grounded = try_grounded_chat_reply(raw, session_id=session_id, channel=channel)
    if grounded is not None:
        body, intent, meta = grounded
        return ChatTurnResult(
            reply=body,
            intent=intent,
            provider_stream=False,
            used_llm=False,
            meta=meta,
        )

    from aethos_core.conversation.entity_compat import try_operational_continuity_guard

    continuity = try_operational_continuity_guard(raw, session_id=session_id, channel=channel)
    if continuity is not None:
        body, intent, meta = continuity
        return ChatTurnResult(
            reply=body,
            intent=intent,
            provider_stream=False,
            used_llm=False,
            meta=meta,
        )

    return None


def _try_extended_operational_routers(
    raw: str,
    *,
    session_id: str,
    channel: str,
    emotional_context: dict[str, object] | None,
) -> "ChatTurnResult | None":
    from aethos_core.chat.service import ChatTurnResult

    _ = emotional_context

    from aethos_core.providers.railway.deployment_readiness.railway_credential_diagnostics import (
        route_railway_credential_diagnostics,
    )

    credential_diag = route_railway_credential_diagnostics(raw, session_id=session_id)
    if credential_diag is not None:
        return _tuple_result(credential_diag, session_id=session_id)

    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_diagnostics_router import (
        route_railway_deployment_lifecycle_diagnostics,
    )

    lifecycle_diag = route_railway_deployment_lifecycle_diagnostics(raw, session_id=session_id)
    if lifecycle_diag is not None:
        return _tuple_result(lifecycle_diag, session_id=session_id)

    from aethos_core.providers.railway.deployment_plan.deployment_plan_router import (
        route_railway_new_service_plan,
    )

    plan_result = route_railway_new_service_plan(raw, session_id=session_id)
    if plan_result is not None:
        return _tuple_result(plan_result, session_id=session_id)

    from aethos_core.providers.railway.deployment_plan.creation_preflight_router import (
        route_railway_service_creation_preflight,
    )

    preflight_result = route_railway_service_creation_preflight(raw, session_id=session_id)
    if preflight_result is not None:
        return _tuple_result(preflight_result, session_id=session_id)

    from aethos_core.providers.railway.env_value_readiness.env_value_router import (
        route_railway_env_value_readiness,
    )

    env_value_result = route_railway_env_value_readiness(raw, session_id=session_id)
    if env_value_result is not None:
        return _tuple_result(env_value_result, session_id=session_id)

    from aethos_core.providers.railway.service_creation_simulator.simulator_router import (
        route_railway_service_creation_simulator,
    )

    simulator_result = route_railway_service_creation_simulator(raw, session_id=session_id)
    if simulator_result is not None:
        return _tuple_result(simulator_result, session_id=session_id)

    from aethos_core.runtime_truth_alignment.runtime_truth_alignment_router import route_runtime_truth_alignment

    runtime_truth = route_runtime_truth_alignment(raw, session_id=session_id)
    if runtime_truth is not None:
        return _tuple_result(runtime_truth, session_id=session_id)

    from aethos_core.mission_control.mission_control_router import route_mission_control_observability

    mission_control_result = route_mission_control_observability(raw, session_id=session_id)
    if mission_control_result is not None:
        return _tuple_result(mission_control_result, session_id=session_id)

    from aethos_core.provider_delivery.github_delivery_capability_router import route_github_delivery_capability

    github_delivery = route_github_delivery_capability(raw, session_id=session_id)
    if github_delivery is not None:
        return _tuple_result(github_delivery, session_id=session_id)

    from aethos_core.software_delivery.software_delivery_router import route_software_delivery

    software_delivery_result = route_software_delivery(raw, session_id=session_id)
    if software_delivery_result is not None:
        return _tuple_result(software_delivery_result, session_id=session_id)

    from aethos_core.providers.railway.execution_contract.production_incident_command_router import (
        route_railway_production_incident_command,
    )

    incident_command_result = route_railway_production_incident_command(raw, session_id=session_id)
    if incident_command_result is not None:
        return _tuple_result(incident_command_result, session_id=session_id)

    from aethos_core.providers.railway.execution_contract.production_canary_shadow_policy_router import (
        route_railway_production_canary_shadow_policy,
    )

    canary_shadow_policy_result = route_railway_production_canary_shadow_policy(raw, session_id=session_id)
    if canary_shadow_policy_result is not None:
        return _tuple_result(canary_shadow_policy_result, session_id=session_id)

    from aethos_core.providers.railway.execution_contract.production_rollout_router import (
        route_railway_production_rollout,
    )

    production_rollout_result = route_railway_production_rollout(raw, session_id=session_id)
    if production_rollout_result is not None:
        return _tuple_result(production_rollout_result, session_id=session_id)

    from aethos_core.providers.railway.execution_contract.production_rollback_escalation_router import (
        route_railway_production_rollback_escalation,
    )

    rollback_escalation_result = route_railway_production_rollback_escalation(raw, session_id=session_id)
    if rollback_escalation_result is not None:
        return _tuple_result(rollback_escalation_result, session_id=session_id)

    from aethos_core.providers.railway.execution_contract.production_verification_router import (
        route_railway_production_verification,
    )

    production_verification_result = route_railway_production_verification(raw, session_id=session_id)
    if production_verification_result is not None:
        return _tuple_result(production_verification_result, session_id=session_id)

    from aethos_core.providers.railway.execution_contract.production_shadow_router import (
        route_railway_production_shadow,
    )

    production_shadow_result = route_railway_production_shadow(raw, session_id=session_id)
    if production_shadow_result is not None:
        return _tuple_result(production_shadow_result, session_id=session_id)

    from aethos_core.providers.railway.execution_contract.execution_router import (
        route_railway_execution_contract,
    )

    execution_contract_result = route_railway_execution_contract(raw, session_id=session_id)
    if execution_contract_result is not None:
        return _tuple_result(execution_contract_result, session_id=session_id)

    from aethos_core.browser_observation.browser_observation_router import (
        is_browser_observation_lane_intent,
        route_browser_observation_lane,
    )

    if is_browser_observation_lane_intent(raw):
        observation = route_browser_observation_lane(raw, session_id=session_id)
        if observation is not None:
            return _tuple_result(observation, session_id=session_id)

    from aethos_core.chat.local_system_guidance import route_local_system_guidance

    local_guidance = route_local_system_guidance(raw, session_id=session_id)
    if local_guidance is not None:
        return _tuple_result(local_guidance, session_id=session_id)

    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_intent import (
        is_railway_deployment_readiness_intent,
    )
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_safe_runtime import (
        safe_route_railway_deployment_readiness,
    )

    if is_railway_deployment_readiness_intent(raw):
        readiness = safe_route_railway_deployment_readiness(raw, session_id=session_id)
        if readiness is not None:
            return _tuple_result(readiness, session_id=session_id)

    from aethos_core.providers.github.workflow_lane.workflow_lane_router import (
        is_workflow_lane_intent,
        route_workflow_lane,
    )

    if is_workflow_lane_intent(raw):
        lane_result = route_workflow_lane(raw, session_id=session_id)
        if lane_result is not None:
            return _tuple_result(lane_result, session_id=session_id)

    return None


def try_single_loop_turn(
    raw: str,
    *,
    session_id: str,
    channel: str,
    surface: str = "webchat",
    model_override: str | None = None,
    tenant_id: str | None = None,
) -> "ChatTurnResult | None":
    """Single-loop chat — governed mutation gate, then model tool loop (§2).

    No router scramble: questions, follow-ups, and writing requests never hit
    operational report builders or deployment-target resolvers.
    """
    from aethos_core.chat.explicit_mutation_intent import compose_explicit_mutation_preflight_reply
    from aethos_core.chat.service import ChatTurnResult, _handled_to_result
    from aethos_core.provider.completion import ProviderResult, complete_chat

    mutation = compose_explicit_mutation_preflight_reply(raw, session_id=session_id)
    if mutation is not None:
        body, intent, meta = mutation
        meta = dict(meta)
        meta["session_id"] = session_id
        meta["single_loop"] = "true"
        meta["real_mutation_action"] = "true"
        meta["lane"] = "single_loop_mutation"
        return _tuple_result((body, intent, meta), session_id=session_id)

    from aethos_core.channels.channel_registry import compose_channel_health_reply, is_channel_health_request

    if is_channel_health_request(raw):
        channel_health = compose_channel_health_reply(raw)
        if channel_health is not None:
            return _handled_to_result(channel_health)

    # External research ("research …", "cite sources", "look up", "web search") must never be
    # hijacked by the provider-inventory or operational-cognition lanes below just because it
    # names a provider (Railway/Vercel) or a failed service. Route it to the agent runtime
    # (deep research / web tools) and fall back to a direct model answer.
    if is_external_research_request(raw):
        research_agent = try_agent_runtime_turn(
            raw,
            session_id=session_id,
            channel=channel,
            surface=surface,
            model_override=model_override,
            tenant_id=tenant_id,
        )
        if research_agent is not None:
            meta = dict(research_agent.meta or {})
            meta["single_loop"] = "true"
            meta.setdefault("session_id", session_id)
            meta.setdefault("lane", "research")
            research_agent.meta = meta
            return research_agent
        from aethos_core.provider.completion import complete_chat as _complete_research

        prov = _complete_research(raw, session_id=session_id, channel=channel, model_override=model_override)
        return ChatTurnResult(
            reply=prov.text,
            intent="research_answer",
            used_llm=prov.used_llm,
            provider=prov.provider,
            model=prov.model,
            meta={"lane": "research", "single_loop": "true", "session_id": session_id},
        )

    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_safe_runtime import (
        safe_route_railway_deployment_readiness,
    )

    deploy_readiness = safe_route_railway_deployment_readiness(raw, session_id=session_id)
    if deploy_readiness is not None:
        body, intent, meta = deploy_readiness
        meta = dict(meta)
        meta["single_loop"] = "true"
        meta.setdefault("session_id", session_id)
        meta.setdefault("lane", "deployment_readiness")
        return _tuple_result((body, intent, meta), session_id=session_id)

    from aethos_core.chat.railway_readonly_prompts import create_railway_readonly_job_reply

    railway_readonly = create_railway_readonly_job_reply(raw, session_id=session_id)
    if railway_readonly is not None:
        body, intent, meta = railway_readonly
        meta = dict(meta)
        meta["single_loop"] = "true"
        meta.setdefault("session_id", session_id)
        return _tuple_result((body, intent, meta), session_id=session_id)

    from aethos_core.chat.engineering_intelligence import execute_engineering_intent, is_engineering_intelligence_request

    if is_engineering_intelligence_request(raw):
        handled = execute_engineering_intent(raw, session_id=session_id)
        if handled:
            body, intent, meta = handled
            meta = dict(meta)
            meta["single_loop"] = "true"
            meta.setdefault("session_id", session_id)
            return _tuple_result((body, intent, meta), session_id=session_id)

    from aethos_core.chat.deterministic import is_canvas_render_request

    if is_canvas_render_request(raw):
        agent = try_agent_runtime_turn(
            raw,
            session_id=session_id,
            channel=channel,
            surface=surface,
            model_override=model_override,
            tenant_id=tenant_id,
        )
        if agent is not None:
            meta = dict(agent.meta or {})
            meta["single_loop"] = "true"
            meta.setdefault("session_id", session_id)
            agent.meta = meta
            _save_trace(session_id, meta, agent.intent)
            return agent

    from aethos_core.chat.provider_read_intent import compose_provider_read_inventory_reply

    provider_read = compose_provider_read_inventory_reply(raw, session_id=session_id)
    if provider_read is not None:
        body, intent, meta = provider_read
        meta = dict(meta)
        meta["single_loop"] = "true"
        meta.setdefault("session_id", session_id)
        return _tuple_result((body, intent, meta), session_id=session_id)

    from aethos_core.chat.provider_read_intent import (
        compose_provider_health_followup_reply,
        try_compose_inventory_rerender_reply,
    )

    inventory_rerender = try_compose_inventory_rerender_reply(raw, session_id=session_id)
    if inventory_rerender is not None:
        body, intent, meta = inventory_rerender
        meta = dict(meta)
        meta["single_loop"] = "true"
        meta.setdefault("session_id", session_id)
        return _tuple_result((body, intent, meta), session_id=session_id)

    health_followup = compose_provider_health_followup_reply(raw, session_id=session_id)
    if health_followup is not None:
        body, intent, meta = health_followup
        meta = dict(meta)
        meta["single_loop"] = "true"
        meta.setdefault("session_id", session_id)
        return _tuple_result((body, intent, meta), session_id=session_id)

    from aethos_core.response_composition.response_composer import try_compose_rerender_reply

    rerender = try_compose_rerender_reply(raw, session_id=session_id)
    if rerender is not None:
        body, intent, meta = rerender
        meta = dict(meta)
        meta["single_loop"] = "true"
        meta.setdefault("session_id", session_id)
        return _tuple_result((body, intent, meta), session_id=session_id)

    from aethos_core.chat.front_door_intent import should_skip_operational_cognition

    if not should_skip_operational_cognition(raw):
        from aethos_core.chat.cognition_exception_boundary import safe_resolve_operational_turn

        operational = safe_resolve_operational_turn(raw, session_id=session_id, channel=channel)
        if operational is not None:
            meta = dict(operational.meta or {})
            meta["single_loop"] = "true"
            meta.setdefault("session_id", session_id)
            operational.meta = meta
            return operational

    agent = try_agent_runtime_turn(
        raw,
        session_id=session_id,
        channel=channel,
        surface=surface,
        model_override=model_override,
        tenant_id=tenant_id,
    )
    if agent is not None:
        meta = dict(agent.meta or {})
        meta["single_loop"] = "true"
        meta.setdefault("session_id", session_id)
        meta.setdefault("lane", "single_loop_agent")
        agent.meta = meta
        _save_trace(session_id, meta, agent.intent)
        return agent

    from aethos_core.chat.conversation_context import compose_conversation_llm_context

    overlay = compose_conversation_llm_context(session_id) or ""
    if overlay:
        overlay = (
            "Single-loop fallback — answer from conversation memory; write prose when asked.\n\n"
            + overlay
        )
    prov: ProviderResult = complete_chat(
        raw,
        session_id=session_id,
        channel=channel,
        system_overlay=overlay or None,
        model_override=model_override,
    )
    return ChatTurnResult(
        reply=prov.text,
        intent="single_loop_answer",
        provider_stream=False,
        used_llm=prov.used_llm,
        provider=prov.provider,
        model=prov.model,
        meta={
            "lane": "single_loop_fallback",
            "single_loop": "true",
            "session_id": session_id,
            "suppress_governance_footer": "true",
        },
    )


def try_agent_runtime_turn(
    raw: str,
    *,
    session_id: str,
    channel: str,
    model_override: str | None = None,
    surface: str = "webchat",
    tenant_id: str | None = None,
) -> "ChatTurnResult | None":
    """Step 3 — LLM tool loop, then provider fallback."""
    from aethos_core.execution_brain.agent_runtime import agent_runtime_chat_turn
    from aethos_core.post_mutation_verification.global_verification_preemption import (
        route_global_verification_query,
    )

    agent = agent_runtime_chat_turn(
        raw,
        session_id=session_id,
        channel=channel,
        model_override=model_override,
        tenant_id=tenant_id,
        surface=surface,
    )
    if agent is not None:
        _save_trace(session_id, {k: str(v) for k, v in agent.meta.items()}, agent.intent)
        return agent

    llm_guard = route_global_verification_query(raw, session_id=session_id)
    if llm_guard is not None:
        return llm_guard

    from aethos_core.provider.completion import ProviderResult, complete_chat

    prov: ProviderResult = complete_chat(raw, session_id=session_id, channel=channel, model_override=model_override)
    from aethos_core.continuity_intelligence.conversational_identity_runtime import guard_generative_amnesia
    from aethos_core.chat.service import ChatTurnResult

    guarded = guard_generative_amnesia(
        user_text=raw,
        session_id=session_id,
        reply=prov.text,
        intent="generative_answer",
    )
    if guarded is not None:
        body, intent, meta = guarded
        return ChatTurnResult(
            reply=body,
            intent=intent,
            provider_stream=False,
            used_llm=False,
            meta=dict(meta),
        )
    return ChatTurnResult(
        reply=prov.text,
        intent="generative_answer",
        provider_stream=False,
        used_llm=prov.used_llm,
        provider=prov.provider,
        model=prov.model,
        meta={"lane": "provider"},
    )
