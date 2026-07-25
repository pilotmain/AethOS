# SPDX-License-Identifier: Apache-2.0
"""Operational cognition graph — single authoritative operational reasoning runtime."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from aethos_core.capabilities.capability_executor import CapabilityExecutionResult, execute_cognition_strategy
from aethos_core.operational_cognition.cognition_memory_bridge import load_cognition_memory
from aethos_core.operational_cognition.operational_intent_engine import interpret_operational_intent
from aethos_core.operational_cognition.semantic_scope_engine import resolve_semantic_scope
from aethos_core.operational_cognition.types import OperationalCognitionDecision

if TYPE_CHECKING:
    from aethos_core.chat.operational_master_router import OperationalRouteDecision

_log = logging.getLogger(__name__)


def plan_operational_cognition(
    text: str,
    *,
    session_id: str = "default",
) -> OperationalCognitionDecision:
    memory = load_cognition_memory(session_id=session_id)
    scope_decision = resolve_semantic_scope(text, session_id=session_id, memory=memory)
    intent_decision = interpret_operational_intent(text, session_id=session_id, memory=memory)

    reasoning = [
        f"scope={scope_decision.scope} ({scope_decision.reason})",
        f"intent={intent_decision.intent} (confidence={intent_decision.confidence:.2f})",
    ]
    if memory.has_provider_wide_health:
        reasoning.append(f"cached_health_failed={memory.failed_service_count}")
    if memory.has_active_thread and not scope_decision.overrides_active_thread:
        reasoning.append(f"active_thread={memory.active_provider}/{memory.active_service}")

    decision = OperationalCognitionDecision(
        intent=intent_decision.intent,
        scope=scope_decision.scope,
        provider=intent_decision.provider,
        target=intent_decision.target,
        confidence=intent_decision.confidence,
        reasoning_chain=reasoning + intent_decision.signals,
        execution_strategy=_execution_strategy_for(intent_decision.intent, scope_decision.scope),
        meta={
            "overrides_active_thread": scope_decision.overrides_active_thread,
            "scope_reason": scope_decision.reason,
        },
    )
    from aethos_core.capabilities.capability_planner import attach_capabilities

    return attach_capabilities(decision, session_id=session_id)


def _execution_strategy_for(intent: str, scope: str) -> str:
    if intent == "inspect_route_trace":
        return "internal_diagnostics"
    if intent == "transform_response":
        return "provider_wide_planner"
    if intent in {"diagnose_failure", "fetch_logs", "fetch_events", "create_fix_plan"}:
        return "failed_service_preemption"
    if intent in {"inventory_health_report", "inventory_list"}:
        return "provider_wide_planner"
    if intent == "mutation":
        return "explicit_mutation"
    if scope == "active_target":
        return "active_thread_followup"
    return "cognition_graph"


def resolve_operational_cognition(
    text: str,
    *,
    session_id: str = "default",
    channel: str = "chat",
    stop_before: str | None = None,
) -> "OperationalRouteDecision | None":
    raw = (text or "").strip()
    if not raw:
        return None

    from aethos_core.chat.route_trace import compose_internal_route_trace_reply
    from aethos_core.chat.operational_master_router import OperationalRouteDecision
    from aethos_core.post_mutation_verification.global_verification_preemption import (
        route_global_verification_query,
    )

    internal = compose_internal_route_trace_reply(raw, session_id=session_id)
    if internal is not None:
        reply, intent, meta = internal
        return OperationalRouteDecision(
            reply=reply,
            intent=intent,
            meta={k: str(v) for k, v in meta.items()},
            route_id="internal_diagnostics",
            matched_module="chat.route_trace",
            trace_chain=["operational_cognition", "internal_diagnostics", intent],
        )

    global_verification = route_global_verification_query(raw, session_id=session_id)
    if global_verification is not None:
        meta = {k: str(v) for k, v in (global_verification.meta or {}).items()}
        route_id = str(meta.get("route_id") or "post_mutation_verification")
        return OperationalRouteDecision(
            reply=global_verification.reply,
            intent=global_verification.intent,
            meta=meta,
            route_id=route_id,
            matched_module="post_mutation_verification.global_verification_preemption",
            trace_chain=["operational_cognition", route_id, global_verification.intent],
        )

    from aethos_core.repair_memory.repair_outcome_router import route_repair_outcome_question

    repair_outcome = route_repair_outcome_question(raw, session_id=session_id)
    if repair_outcome is not None:
        meta = {k: str(v) for k, v in (repair_outcome.meta or {}).items()}
        return OperationalRouteDecision(
            reply=repair_outcome.reply,
            intent=repair_outcome.intent,
            meta=meta,
            route_id="repair_outcome",
            matched_module="repair_memory.repair_outcome_router",
            trace_chain=["operational_cognition", "repair_outcome", repair_outcome.intent],
        )

    from aethos_core.providers.github.mutations.rerun_no_execution_followup import (
        compose_rerun_no_execution_followup,
    )

    no_exec = compose_rerun_no_execution_followup(raw, session_id=session_id)
    if no_exec is not None:
        reply, intent, meta = no_exec
        return OperationalRouteDecision(
            reply=reply,
            intent=intent,
            meta={k: str(v) for k, v in meta.items()},
            route_id=str(meta.get("route_id") or "github_rerun_no_execution"),
            matched_module="providers.github.mutations.rerun_no_execution_followup",
            trace_chain=["operational_cognition", "github_rerun_no_execution", intent],
        )

    from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
        route_workflow_discovery_followup,
    )

    workflow_discovery = route_workflow_discovery_followup(raw, session_id=session_id)
    if workflow_discovery is not None:
        reply, intent, meta = workflow_discovery
        return OperationalRouteDecision(
            reply=reply,
            intent=intent,
            meta={k: str(v) for k, v in meta.items()},
            route_id=str(meta.get("route_id") or "workflow_discovery_followup"),
            matched_module="providers.github.workflow_discovery.workflow_discovery_followup_router",
            trace_chain=["operational_cognition", "workflow_discovery_followup", intent],
        )

    from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
        route_workflow_discovery_hard_preemption,
        route_workflow_discovery_followup,
    )

    hard_workflow = route_workflow_discovery_hard_preemption(raw, session_id=session_id)
    if hard_workflow is not None:
        reply, intent, meta = hard_workflow
        return OperationalRouteDecision(
            reply=reply,
            intent=intent,
            meta={k: str(v) for k, v in meta.items()},
            route_id=str(meta.get("route_id") or "workflow_discovery_followup"),
            matched_module="providers.github.workflow_discovery.workflow_discovery_followup_router",
            trace_chain=["operational_cognition", "workflow_discovery_hard_preemption", intent],
        )

    from aethos_core.world_model.investigation_strategy_router import route_investigation_strategy_question

    strategy = route_investigation_strategy_question(raw, session_id=session_id)
    if strategy is not None:
        meta = {k: str(v) for k, v in (strategy.meta or {}).items()}
        return OperationalRouteDecision(
            reply=strategy.reply,
            intent=strategy.intent,
            meta=meta,
            route_id="investigation_strategy",
            matched_module="world_model.investigation_strategy_router",
            trace_chain=["operational_cognition", "investigation_strategy", strategy.intent],
        )

    from aethos_core.providers.railway.deployment_plan.deployment_plan_router import route_railway_new_service_plan
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_safe_runtime import (
        safe_route_railway_deployment_readiness,
    )

    railway_plan = route_railway_new_service_plan(raw, session_id=session_id)
    if railway_plan is not None:
        reply, intent, meta = railway_plan
        return OperationalRouteDecision(
            reply=reply,
            intent=intent,
            meta={k: str(v) for k, v in meta.items()},
            route_id="railway_deployment_plan",
            matched_module="providers.railway.deployment_plan.deployment_plan_router",
            trace_chain=["operational_cognition", "railway_deployment_plan", intent],
        )

    railway_readiness = safe_route_railway_deployment_readiness(raw, session_id=session_id)
    if railway_readiness is not None:
        reply, intent, meta = railway_readiness
        return OperationalRouteDecision(
            reply=reply,
            intent=intent,
            meta={k: str(v) for k, v in meta.items()},
            route_id="railway_deployment_readiness",
            matched_module="providers.railway.deployment_readiness.deployment_readiness_router",
            trace_chain=["operational_cognition", "railway_deployment_readiness", intent],
        )

    from aethos_core.devops_intent_planner.devops_capability_router import route_devops_capability_question

    devops_capability = route_devops_capability_question(raw, session_id=session_id)
    if devops_capability is not None:
        meta = {k: str(v) for k, v in (devops_capability.meta or {}).items()}
        route_id = str(meta.get("route_id") or "devops_capability")
        return OperationalRouteDecision(
            reply=devops_capability.reply,
            intent=devops_capability.intent,
            meta=meta,
            route_id=route_id,
            matched_module="devops_intent_planner.devops_capability_router",
            trace_chain=["operational_cognition", route_id, devops_capability.intent],
        )

    from aethos_core.providers.github.mutations.rerun_intent_continuation import compose_github_workflow_rerun_route_reply

    github_rerun = compose_github_workflow_rerun_route_reply(raw, session_id=session_id)
    if github_rerun is not None:
        reply, intent, meta = github_rerun
        return OperationalRouteDecision(
            reply=reply,
            intent=intent,
            meta={k: str(v) for k, v in meta.items()},
            route_id=str(meta.get("route_id") or "github_workflow_rerun"),
            matched_module="providers.github.mutations.rerun_intent_continuation",
            trace_chain=["operational_cognition", "github_workflow_rerun", intent],
        )

    from aethos_core.browser_observation.browser_observation_router import (
        is_browser_observation_lane_intent,
        route_browser_observation_lane,
    )

    if is_browser_observation_lane_intent(raw):
        observation = route_browser_observation_lane(raw, session_id=session_id)
        if observation is not None:
            reply, intent, meta = observation
            return OperationalRouteDecision(
                reply=reply,
                intent=intent,
                meta={k: str(v) for k, v in meta.items()},
                route_id="browser_observation",
                matched_module="browser_observation.browser_observation_router",
                trace_chain=["operational_cognition", "browser_observation", intent],
            )

    from aethos_core.provider_readonly_intent.readonly_provider_router import route_readonly_provider_question

    readonly_provider = route_readonly_provider_question(raw, session_id=session_id)
    if readonly_provider is not None:
        meta = {k: str(v) for k, v in (readonly_provider.meta or {}).items()}
        route_id = str(meta.get("route_id") or "provider_readonly_intent")
        return OperationalRouteDecision(
            reply=readonly_provider.reply,
            intent=readonly_provider.intent,
            meta=meta,
            route_id=route_id,
            matched_module="provider_readonly_intent.readonly_provider_router",
            trace_chain=["operational_cognition", route_id, readonly_provider.intent],
        )

    from aethos_core.chat.front_door_router import compose_front_door_route_reply

    front_door = compose_front_door_route_reply(raw, session_id=session_id)
    if front_door is not None:
        reply, intent, meta = front_door
        route_id = str(meta.get("route_id") or "front_door")
        return OperationalRouteDecision(
            reply=reply,
            intent=intent,
            meta={k: str(v) for k, v in meta.items()},
            route_id=route_id,
            matched_module="chat.front_door_router",
            trace_chain=["operational_cognition", route_id, intent],
        )

    decision = plan_operational_cognition(raw, session_id=session_id)
    _log.info("Operational cognition: %s", json.dumps(decision.to_dict()))

    execution = execute_cognition_strategy(decision, raw, session_id=session_id, stop_before=stop_before)

    if not execution.handled:
        return None

    from aethos_core.conversation.continuity_synthesis import naturalize_operational_reply
    from aethos_core.operational_state.state import update_operational_state

    try:
        reply = naturalize_operational_reply(
            execution.reply,
            intent=execution.intent,
            cognition=decision,
        )
    except Exception:
        _log.exception("Operational reply naturalization failed; using raw execution reply")
        reply = execution.reply
    try:
        update_operational_state(
            session_id=session_id,
            intent=decision.intent,
            target=decision.target,
            provider=decision.provider,
            diagnosis_summary=_diagnosis_summary_from_reply(reply, intent=execution.intent),
            evidence_state=_evidence_state_from_reply(reply),
            narrative_line=_narrative_line_from_execution(execution, decision),
        )
    except Exception:
        _log.exception("Operational state update failed; continuing with cognition response")

    from aethos_core.chat.operational_master_router import OperationalRouteDecision, BLOCKED_WHEN_PRIORITY

    meta = dict(execution.meta or {})
    meta["cognition_intent"] = decision.intent
    meta["cognition_scope"] = decision.scope
    meta["cognition_confidence"] = f"{decision.confidence:.2f}"
    meta["cognition_capabilities"] = ",".join(decision.capabilities)
    meta["reasoning_chain"] = " → ".join(decision.reasoning_chain)
    meta["route_id"] = execution.route_id
    meta["matched_module"] = execution.matched_module
    if execution.matched_target:
        meta["matched_target"] = execution.matched_target
    trace = list(execution.trace_chain or [execution.route_id])
    meta["route_trace"] = " → ".join(trace)
    blocked: list[str] = []
    if execution.route_id in {"failed_service_preemption", "world_model_investigation"}:
        blocked = sorted(BLOCKED_WHEN_PRIORITY)
        meta["blocked_routes"] = ",".join(blocked)
    elif execution.meta and execution.meta.get("blocked_routes"):
        blocked = [part.strip() for part in str(execution.meta["blocked_routes"]).split(",") if part.strip()]
        meta["blocked_routes"] = ",".join(blocked)

    return OperationalRouteDecision(
        reply=reply,
        intent=execution.intent,
        meta=meta,
        route_id=execution.route_id,
        matched_module=execution.matched_module,
        blocked_routes=blocked,
        matched_target=execution.matched_target,
        trace_chain=trace,
    )


def _diagnosis_summary_from_reply(reply: str, *, intent: str) -> str:
    if not intent.startswith("failed_service"):
        return ""
    lines = [line.strip() for line in reply.splitlines() if line.strip()]
    for line in lines[:6]:
        if line.startswith("Classification:") or line.startswith("- Summary:"):
            return line
    return lines[0] if lines else ""


def _evidence_state_from_reply(reply: str) -> str:
    low = reply.lower()
    if "insufficient evidence" in low or "not enough log evidence" in low:
        return "insufficient"
    if "logs available: **no**" in low:
        return "insufficient"
    if "logs available: **yes**" in low:
        return "available"
    return "unknown"


def _narrative_line_from_execution(execution: CapabilityExecutionResult, decision: OperationalCognitionDecision) -> str:
    target = execution.matched_target or decision.target or "the active target"
    if execution.intent == "failed_service_diagnosis":
        return f"Investigated failed service {target} and produced a bounded diagnosis."
    if execution.intent == "failed_service_fix_plan":
        return f"Drafted an evidence-based fix plan for {target}."
    if execution.intent.startswith("world_model_"):
        return f"Continued the active investigation for {target}."
    if execution.intent == "operational_narrative_continuity":
        return "Recapped recent operational continuity."
    if execution.intent.startswith("operational_response"):
        return f"Rendered provider-wide operational results ({decision.intent})."
    return ""
