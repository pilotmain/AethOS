# SPDX-License-Identifier: Apache-2.0
"""Capability executor — runs capability chains with bounded failure behavior."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable

CallableType = Callable[..., tuple[str, str, dict[str, str]] | None]

from aethos_core.operational_cognition.types import OperationalCognitionDecision


@dataclass
class CapabilityExecutionResult:
    handled: bool
    reply: str = ""
    intent: str = ""
    meta: dict[str, str] | None = None
    route_id: str = ""
    matched_module: str = ""
    matched_target: str = ""
    trace_chain: list[str] | None = None
    partial: bool = False
    errors: list[str] | None = None


_HANDLERS_CACHE: list[tuple[str, str, CallableType]] | None = None


def _cognition_handlers() -> list[tuple[str, str, CallableType]]:
    """Ordered (route_id, module, handler) registry — built once, reused per turn.

    The handler functions are module-level, so the registry is a constant; building
    it once avoids re-allocating ~30 tuples on every chat turn (§C1). Routing order
    and first-match-wins semantics are unchanged.
    """
    global _HANDLERS_CACHE
    if _HANDLERS_CACHE is not None:
        return _HANDLERS_CACHE
    _HANDLERS_CACHE = [
        ("agent_orchestration", "execution_brain.agent_runtime", _try_agent_orchestration),
        ("identity_contract", "aethos_identity.identity_contract_loader", _try_identity_contract),
        ("internal_diagnostics", "chat.route_trace", _try_internal_diagnostics),
        ("provider_readonly_intent", "provider_readonly_intent.readonly_provider_router", _try_provider_readonly),
        ("post_mutation_verification", "post_mutation_verification.global_verification_preemption", _try_global_verification_preemption),
        ("front_door", "chat.front_door_router", _try_front_door),
        ("github_rerun_no_execution", "providers.github.mutations.rerun_no_execution_followup", _try_github_rerun_no_execution),
        ("workflow_discovery_followup", "providers.github.workflow_discovery.workflow_discovery_followup_router", _try_workflow_discovery_followup),
        ("operation_lifecycle", "operation_lifecycle.lifecycle_followup_router", _try_operation_lifecycle),
        ("post_mutation_verification", "post_mutation_verification.verification_followup_router", _try_post_mutation_verification),
        ("repair_outcome", "repair_memory.repair_outcome_router", _try_repair_outcome),
        ("investigation_strategy", "world_model.investigation_strategy_router", _try_investigation_strategy),
        (
            "railway_deployment_plan",
            "providers.railway.deployment_plan.deployment_plan_router",
            _try_railway_deployment_plan,
        ),
        (
            "railway_deployment_readiness",
            "providers.railway.deployment_readiness.deployment_readiness_router",
            _try_railway_deployment_readiness,
        ),
        ("local_system_guidance", "chat.local_system_guidance", _try_local_system_guidance),
        ("email_imap_setup_guidance", "chat.email_imap_setup_guidance", _try_email_imap_setup_guidance),
        ("devops_capability", "devops_intent_planner.devops_capability_router", _try_devops_capability),
        ("world_model_investigation", "world_model.world_model_followup_router", _try_world_model_followup),
        ("explicit_mutation", "chat.explicit_mutation_intent", _try_explicit_mutation),
        ("provider_wide_planner", "operational_planner.planner_router", _try_provider_wide_planner),
        ("failed_service_preemption", "failed_service_investigation.global_preemption", _try_failed_service),
        ("operational_narrative", "operational_state.narrative", _try_operational_narrative),
        ("source_binding_correction", "provider_topology.source_binding_chat", _try_source_binding),
        ("pending_action_continuation", "task_frame.confirmation_continuation", _try_pending_action),
        ("task_continuation", "task_frame.task_continuation", _try_task_continuation),
        ("railway_redeploy_continuation", "task_frame.railway_redeploy_continuation", _try_railway_redeploy_continuation),
        ("retry_active_operation", "task_frame.retry_active_operation", _try_retry_operation),
        ("cross_provider_correlation", "cross_provider_correlation.correlation_router", _try_cross_provider_correlation),
        ("github_workflow_rerun", "providers.github.mutations.rerun_intent_continuation", _try_github_workflow_rerun),
        ("provider_followup", "conversation.provider_memory.conversational_memory_router", _try_provider_followup),
        ("active_thread_followup", "operational_thread_memory.thread_reply_composer", _try_thread_followup),
    ]
    return _HANDLERS_CACHE


def execute_cognition_strategy(
    decision: OperationalCognitionDecision,
    text: str,
    *,
    session_id: str = "default",
    stop_before: str | None = None,
) -> CapabilityExecutionResult:
    from aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context import (
        enforce_workflow_discovery_absolute_lane,
    )
    from aethos_core.chat.lane_hydration import maybe_hydrate_lane_contexts

    maybe_hydrate_lane_contexts(text=text, session_id=session_id)

    from aethos_core.browser_observation.browser_observation_router import (
        is_browser_observation_lane_intent,
        route_browser_observation_lane,
    )

    if is_browser_observation_lane_intent(text):
        observation = route_browser_observation_lane(text, session_id=session_id)
        if observation is not None:
            reply, intent, meta = observation
            return CapabilityExecutionResult(
                handled=True,
                reply=reply,
                intent=intent,
                meta={k: str(v) for k, v in meta.items()},
                route_id="browser_observation",
                matched_module="browser_observation.browser_observation_router",
                trace_chain=["operational_cognition", "browser_observation", intent],
            )

    absolute = enforce_workflow_discovery_absolute_lane(text, session_id=session_id)
    if absolute is not None:
        reply, intent, meta = absolute
        return CapabilityExecutionResult(
            handled=True,
            reply=reply,
            intent=intent,
            meta={k: str(v) for k, v in meta.items()},
            route_id=str(meta.get("route_id") or "workflow_discovery_followup"),
            matched_module="providers.github.workflow_discovery.workflow_discovery_runtime_context",
            trace_chain=["operational_cognition", "workflow_discovery_runtime_binding", intent],
        )

    handlers = _cognition_handlers()

    stop_points = {
        "internal_diagnostics": 1,
        "provider_readonly_intent": 2,
        "post_mutation_verification": 3,
        "front_door": 4,
        "operation_lifecycle": 5,
        "repair_outcome": 5,
        "investigation_strategy": 5,
        "railway_deployment_plan": 5,
        "railway_deployment_readiness": 5,
        "local_system_guidance": 6,
        "devops_capability": 5,
        "world_model_investigation": 6,
        "explicit_mutation": 7,
        "failed_service_preemption": 9,
        "operational_narrative": 10,
        "source_binding_correction": 11,
        "pending_action_continuation": 12,
        "github_workflow_rerun": 14,
        "provider_followup": 15,
        "active_thread_followup": 16,
        "readonly_provider_diagnostics": len(handlers),
    }

    max_index = stop_points.get(stop_before or "", len(handlers) + 10)

    for idx, (route_id, module, handler) in enumerate(handlers):
        if stop_before and idx >= max_index:
            break
        if _is_route_blocked(route_id):
            continue
        handled = handler(text, session_id=session_id)
        if handled is None:
            continue
        reply, intent, meta = handled
        target = _target_from_meta(meta)
        trace = ["operational_cognition"] + decision.capabilities[:3] + [route_id, intent]
        return CapabilityExecutionResult(
            handled=True,
            reply=reply,
            intent=intent,
            meta={k: str(v) for k, v in meta.items()},
            route_id=route_id,
            matched_module=module,
            matched_target=target,
            trace_chain=trace,
        )

    if stop_before in {None, "readonly_provider_diagnostics"} and not _is_route_blocked("readonly_provider_diagnostics"):
        readonly = _try_readonly_diagnostics(text, session_id=session_id)
        if readonly is not None:
            return readonly
    if stop_before in {None, "browser_vercel_diagnostics", "continuity_reconstruction"}:
        if not _is_route_blocked("browser_vercel_diagnostics"):
            browser = _try_browser_vercel(text, session_id=session_id)
            if browser is not None:
                return browser
        if not _is_route_blocked("continuity_reconstruction"):
            continuity = _try_continuity(text, session_id=session_id)
            if continuity is not None:
                return continuity

    return CapabilityExecutionResult(handled=False)


def _is_route_blocked(route_id: str) -> bool:
    _ = route_id
    return False


def _target_from_meta(meta: dict[str, str]) -> str:
    project = str(meta.get("project") or "—")
    environment = str(meta.get("environment") or "—")
    service = str(meta.get("service") or "—")
    if service != "—":
        return f"{project} / {environment} / {service}"
    matched = str(meta.get("matched_target") or "")
    return matched


def _try_agent_orchestration(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    """Highest-priority lane: explicit command-center / multi-agent orchestration.

    Routes a fresh orchestration ask to the agent-runtime orchestration lane
    before any world-model follow-up router can greedily claim it. Declines
    (returns ``None``) for everything else so the rest of the chain is unchanged.
    """
    from aethos_core.agents.runtime.planner import is_command_center_orchestration_request

    if not is_command_center_orchestration_request(text, session_id=session_id):
        return None

    from aethos_core.config import get_settings

    settings = get_settings()
    if not settings.agent_runtime_enabled:
        return (
            "Multi-agent orchestration needs `AGENT_RUNTIME_ENABLED` — it's currently off.\n\n"
            "Set `AGENT_RUNTIME_ENABLED=true` and restart the runtime, and I'll spin up the agents, "
            "populate **Mission Control → Orchestration**, and coordinate them on this.",
            "agent_runtime_disabled",
            {
                "lane": "agent_runtime_disabled",
                "feature": "multi_agent_orchestration",
                "agent_runtime_enabled": "false",
            },
        )

    if settings.durable_agent_jobs_enabled:
        from aethos_core.chat.agent_intelligence import multi_agent_job_reply

        return multi_agent_job_reply(text, session_id=session_id)

    from aethos_core.chat.agent_intelligence import multi_agent_reply

    return multi_agent_reply(text, session_id=session_id)


def _try_identity_contract(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.aethos_identity.identity_contract_loader import compose_identity_contract_reply

    return compose_identity_contract_reply(text)


def _try_global_verification_preemption(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.post_mutation_verification.global_verification_preemption import (
        route_global_verification_query,
    )

    routed = route_global_verification_query(text, session_id=session_id)
    if routed is None:
        return None
    meta = {k: str(v) for k, v in (routed.meta or {}).items()}
    return routed.reply, routed.intent, meta


def _try_front_door(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.chat.front_door_router import compose_front_door_route_reply

    return compose_front_door_route_reply(text, session_id=session_id)


def _try_post_mutation_verification(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.post_mutation_verification.verification_followup_router import (
        compose_post_mutation_verification_reply,
    )

    return compose_post_mutation_verification_reply(text, session_id=session_id)


def _try_repair_outcome(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.repair_memory.repair_outcome_router import compose_repair_outcome_route_reply

    return compose_repair_outcome_route_reply(text, session_id=session_id)


def _try_investigation_strategy(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.world_model.investigation_strategy_router import compose_investigation_strategy_route_reply

    return compose_investigation_strategy_route_reply(text, session_id=session_id)


def _try_local_system_guidance(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.chat.local_system_guidance import route_local_system_guidance

    return route_local_system_guidance(text, session_id=session_id)


def _try_email_imap_setup_guidance(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.chat.email_imap_setup_guidance import compose_email_imap_setup_reply_if_applicable

    return compose_email_imap_setup_reply_if_applicable(text, session_id=session_id)


def _try_railway_deployment_plan(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.providers.railway.deployment_plan.deployment_plan_router import route_railway_new_service_plan

    return route_railway_new_service_plan(text, session_id=session_id)


def _try_railway_deployment_readiness(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_safe_runtime import (
        safe_route_railway_deployment_readiness,
    )

    return safe_route_railway_deployment_readiness(text, session_id=session_id)


def _try_devops_capability(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.devops_intent_planner.devops_capability_router import compose_devops_capability_route_reply

    return compose_devops_capability_route_reply(text, session_id=session_id)


def _try_github_rerun_no_execution(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.providers.github.mutations.rerun_no_execution_followup import (
        compose_rerun_no_execution_followup,
    )

    return compose_rerun_no_execution_followup(text, session_id=session_id)


def _try_workflow_discovery_followup(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
        route_workflow_discovery_followup,
    )

    return route_workflow_discovery_followup(text, session_id=session_id)


def _try_operation_lifecycle(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.operation_lifecycle.lifecycle_followup_router import compose_lifecycle_followup_reply

    return compose_lifecycle_followup_reply(text, session_id=session_id)


def _try_world_model_followup(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.world_model.safe_world_model_runtime import safe_route_world_model_followup

    return safe_route_world_model_followup(text, session_id=session_id)


def _try_explicit_mutation(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.chat.explicit_mutation_intent import compose_explicit_mutation_preflight_reply

    return compose_explicit_mutation_preflight_reply(text, session_id=session_id)


def _try_provider_wide_planner(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.config import get_settings

    if get_settings().agent_runtime_enabled:
        from aethos_core.execution_brain.agent_provider_cloud import is_agent_provider_cloud_request

        if is_agent_provider_cloud_request(text, session_id=session_id):
            return None

    from aethos_core.operational_planner.planner_router import compose_planned_operational_reply_without_failed_service

    return compose_planned_operational_reply_without_failed_service(text, session_id=session_id)


def _try_failed_service(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.failed_service_investigation.global_preemption import route_failed_service_intent

    return route_failed_service_intent(text, session_id=session_id)


def _try_internal_diagnostics(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.chat.route_trace import compose_internal_route_trace_reply

    return compose_internal_route_trace_reply(text, session_id=session_id)


def _try_operational_narrative(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.operational_state.narrative import compose_narrative_continuity_reply

    return compose_narrative_continuity_reply(text, session_id=session_id)


def _try_source_binding(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.provider_topology.source_binding_chat import compose_source_binding_correction_reply

    return compose_source_binding_correction_reply(text, session_id=session_id)


def _try_pending_action(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.task_frame.confirmation_continuation import compose_pending_action_continuation_reply

    return compose_pending_action_continuation_reply(text, session_id=session_id)


def _try_task_continuation(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.task_frame.task_continuation import compose_task_continuation_reply

    return compose_task_continuation_reply(text, session_id=session_id)


def _try_railway_redeploy_continuation(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.task_frame.railway_redeploy_continuation import compose_railway_redeploy_continuation_reply

    return compose_railway_redeploy_continuation_reply(text, session_id=session_id)


def _try_retry_operation(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.task_frame.retry_active_operation import compose_retry_active_operation_reply

    return compose_retry_active_operation_reply(text, session_id=session_id)


def _try_cross_provider_correlation(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.cross_provider_correlation.correlation_router import route_cross_provider_correlation_question

    return route_cross_provider_correlation_question(text, session_id=session_id)


def _try_github_workflow_rerun(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.providers.github.mutations.rerun_intent_continuation import compose_github_workflow_rerun_route_reply

    return compose_github_workflow_rerun_route_reply(text, session_id=session_id)


def _try_provider_readonly(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.provider_readonly_intent.readonly_provider_router import compose_readonly_provider_route_reply

    return compose_readonly_provider_route_reply(text, session_id=session_id)


def _try_provider_followup(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.conversation.provider_memory.conversational_memory_router import compose_provider_followup_reply

    return compose_provider_followup_reply(text, session_id=session_id)


def _try_thread_followup(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.operational_thread_memory.thread_reply_composer import compose_operational_thread_followup

    return compose_operational_thread_followup(text, session_id=session_id)


def _try_readonly_diagnostics(text: str, *, session_id: str) -> CapabilityExecutionResult | None:
    from aethos_core.chat.operational_master_router import master_router_has_priority_route

    if master_router_has_priority_route(text, session_id=session_id):
        return None
    from aethos_core.chat.railway_readonly_prompts import create_railway_readonly_job_reply
    from aethos_core.chat.github_readonly_prompts import create_github_readonly_job_reply
    from aethos_core.chat.provider_execution_chat import compose_provider_execution_reply
    from aethos_core.chat.provider_discovery_chat import compose_provider_discovery_reply

    for handler, module, label in (
        (create_railway_readonly_job_reply, "chat.railway_readonly_prompts", "railway_readonly"),
        (create_github_readonly_job_reply, "chat.github_readonly_prompts", "github_readonly"),
        (compose_provider_execution_reply, "chat.provider_execution_chat", "provider_execution"),
        (compose_provider_discovery_reply, "chat.provider_discovery_chat", "provider_discovery"),
    ):
        handled = handler(text, session_id=session_id)
        if handled is not None:
            reply, intent, meta = handled
            return CapabilityExecutionResult(
                handled=True,
                reply=reply,
                intent=intent,
                meta={k: str(v) for k, v in meta.items()},
                route_id="readonly_provider_diagnostics",
                matched_module=module,
                trace_chain=["readonly_provider_diagnostics", label],
            )
    return None


def _try_browser_vercel(text: str, *, session_id: str) -> CapabilityExecutionResult | None:
    from aethos_core.chat.operational_master_router import master_router_has_priority_route

    if master_router_has_priority_route(text, session_id=session_id):
        return None
    if re.search(r"\brailway\b", (text or ""), re.I):
        from aethos_core.chat.railway_readonly_prompts import create_railway_readonly_job_reply

        railway = create_railway_readonly_job_reply(text, session_id=session_id)
        if railway is not None:
            reply, intent, meta = railway
            meta = {k: str(v) for k, v in meta.items()}
            return CapabilityExecutionResult(
                handled=True,
                reply=reply,
                intent=intent,
                meta=meta,
                route_id="railway_readonly_direct",
                matched_module="chat.railway_readonly_prompts",
                trace_chain=["railway_readonly_direct"],
            )
    from aethos_core.chat.browser_evidence_prompts import create_browser_evidence_job_reply

    browser_evidence = create_browser_evidence_job_reply(text, session_id=session_id)
    if browser_evidence is not None:
        reply, intent, meta = browser_evidence
        meta = {k: str(v) for k, v in meta.items()}
        meta["blocked_routes"] = "browser_diagnostic"
        return CapabilityExecutionResult(
            handled=True,
            reply=reply,
            intent=intent,
            meta=meta,
            route_id="browser_vercel_diagnostics",
            matched_module="chat.browser_evidence_prompts",
            trace_chain=["browser_vercel_diagnostics", "browser_evidence"],
        )

    from aethos_core.chat.operation_preflight_prompts import create_operation_preflight_job_reply

    operation_preflight = create_operation_preflight_job_reply(text, session_id=session_id)
    if operation_preflight is not None:
        reply, intent, meta = operation_preflight
        meta = {k: str(v) for k, v in meta.items()}
        blocked = ["operation_preflight"]
        if str(meta.get("provider") or "") == "vercel":
            blocked.append("vercel_why_down")
        meta["blocked_routes"] = ",".join(blocked)
        return CapabilityExecutionResult(
            handled=True,
            reply=reply,
            intent=intent,
            meta=meta,
            route_id="browser_vercel_diagnostics",
            matched_module="chat.operation_preflight_prompts",
            trace_chain=["browser_vercel_diagnostics", "operation_preflight"],
        )

    from aethos_core.chat.vercel_readonly_prompts import create_vercel_readonly_job_reply

    vercel_readonly = create_vercel_readonly_job_reply(text, session_id=session_id)
    if vercel_readonly is not None:
        reply, intent, meta = vercel_readonly
        meta = {k: str(v) for k, v in meta.items()}
        meta["blocked_routes"] = "vercel_readonly"
        return CapabilityExecutionResult(
            handled=True,
            reply=reply,
            intent=intent,
            meta=meta,
            route_id="browser_vercel_diagnostics",
            matched_module="chat.vercel_readonly_prompts",
            trace_chain=["browser_vercel_diagnostics", "vercel_readonly"],
        )
    return None


def _try_continuity(text: str, *, session_id: str) -> CapabilityExecutionResult | None:
    from aethos_core.chat.operational_master_router import master_router_has_priority_route

    if master_router_has_priority_route(text, session_id=session_id):
        return None
    from aethos_core.aethos_identity.context_reconstructor import maybe_reconstruct_active_thread
    from aethos_core.aethos_identity.continuity_decision import compose_continuity_operational_reply

    maybe_reconstruct_active_thread(session_id=session_id, user_text=text)
    handled = compose_continuity_operational_reply(text, session_id=session_id)
    if handled is None:
        return None
    reply, intent, meta = handled
    meta = {k: str(v) for k, v in meta.items()}
    meta["blocked_routes"] = "continuity_reconstruction,generic_fix_plan"
    return CapabilityExecutionResult(
        handled=True,
        reply=reply,
        intent=intent,
        meta=meta,
        route_id="continuity_reconstruction",
        matched_module="aethos_identity.continuity_decision",
        trace_chain=["continuity_reconstruction"],
    )
