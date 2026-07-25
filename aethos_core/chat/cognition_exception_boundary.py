# SPDX-License-Identifier: Apache-2.0
"""Server-side exception boundary for operational cognition delivery."""

from __future__ import annotations

import enum
import logging
import uuid
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from aethos_core.chat.service import ChatTurnResult

_log = logging.getLogger(__name__)


@dataclass
class CognitionBoundaryContext:
    text: str
    session_id: str = "default"
    user_id: str = ""
    channel: str = "chat"


def safe_resolve_operational_turn(
    text: str,
    *,
    session_id: str = "default",
    user_id: str = "",
    channel: str = "chat",
    emotional_context: dict[str, object] | None = None,
) -> ChatTurnResult | None:
    """Resolve an operational cognition turn without bubbling exceptions."""
    context = CognitionBoundaryContext(text=text, session_id=session_id, user_id=user_id, channel=channel)
    partial: ChatTurnResult | None = None
    try:
        from aethos_core.chat.provider_read_intent import is_provider_read_inventory_request

        if is_provider_read_inventory_request(text):
            return None

        from aethos_core.providers.railway.deployment_readiness.deployment_readiness_router import (
            route_railway_deployment_readiness,
        )

        readiness = route_railway_deployment_readiness(text, session_id=session_id)
        if readiness is not None:
            reply, intent, meta = readiness
            partial = ChatTurnResult(
                reply=reply,
                intent=intent,
                provider_stream=False,
                used_llm=False,
                meta={k: str(v) for k, v in meta.items()},
            )
            return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.providers.railway.greenfield_deployment.greenfield_router import (
            preemption_chat_turn_result,
        )

        greenfield = preemption_chat_turn_result(
            text,
            session_id=session_id,
            route_source="operational_recall_greenfield_preemption",
        )
        if greenfield is not None:
            return safe_finalize_chat_result(greenfield, context, emotional_context=emotional_context)

        from aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context import (
            enforce_workflow_discovery_absolute_lane_turn,
        )
        from aethos_core.chat.lane_hydration import maybe_hydrate_lane_contexts

        maybe_hydrate_lane_contexts(text=text, session_id=session_id)

        from aethos_core.task_frame.retry_active_operation import compose_retry_active_operation_reply

        retry_result = compose_retry_active_operation_reply(text, session_id=session_id)
        if retry_result is not None:
            body, intent, meta = retry_result
            partial = ChatTurnResult(
                reply=body,
                intent=intent,
                provider_stream=False,
                used_llm=False,
                meta={k: str(v) for k, v in meta.items()},
            )
            from aethos_core.chat.route_trace import save_last_route_trace as _save_retry_trace

            _save_retry_trace(session_id=session_id, meta=meta, intent=intent)
            return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_diagnostics_router import (
            route_railway_deployment_lifecycle_diagnostics,
        )

        lifecycle_diag = route_railway_deployment_lifecycle_diagnostics(text, session_id=session_id)
        if lifecycle_diag is not None:
            reply, intent, meta = lifecycle_diag
            partial = ChatTurnResult(
                reply=reply,
                intent=intent,
                provider_stream=False,
                used_llm=False,
                meta={k: str(v) for k, v in meta.items()},
            )
            from aethos_core.chat.route_trace import save_last_route_trace as _save_lifecycle_diag

            _save_lifecycle_diag(session_id=session_id, meta=meta, intent=intent)
            return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.providers.railway.deployment_plan.deployment_plan_router import (
            route_railway_new_service_plan,
        )

        plan_result = route_railway_new_service_plan(text, session_id=session_id)
        if plan_result is not None:
            reply, intent, meta = plan_result
            partial = ChatTurnResult(
                reply=reply,
                intent=intent,
                provider_stream=False,
                used_llm=False,
                meta={k: str(v) for k, v in meta.items()},
            )
            from aethos_core.chat.route_trace import save_last_route_trace as _save_plan_trace

            _save_plan_trace(session_id=session_id, meta=meta, intent=intent)
            return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.providers.railway.deployment_plan.creation_preflight_router import (
            route_railway_service_creation_preflight,
        )

        preflight_result = route_railway_service_creation_preflight(text, session_id=session_id)
        if preflight_result is not None:
            reply, intent, meta = preflight_result
            partial = ChatTurnResult(
                reply=reply,
                intent=intent,
                provider_stream=False,
                used_llm=False,
                meta={k: str(v) for k, v in meta.items()},
            )
            from aethos_core.chat.route_trace import save_last_route_trace as _save_preflight_trace

            _save_preflight_trace(session_id=session_id, meta=meta, intent=intent)
            return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.providers.railway.env_value_readiness.env_value_router import (
            route_railway_env_value_readiness,
        )

        env_value_result = route_railway_env_value_readiness(text, session_id=session_id)
        if env_value_result is not None:
            reply, intent, meta = env_value_result
            partial = ChatTurnResult(
                reply=reply,
                intent=intent,
                provider_stream=False,
                used_llm=False,
                meta={k: str(v) for k, v in meta.items()},
            )
            from aethos_core.chat.route_trace import save_last_route_trace as _save_env_trace

            _save_env_trace(session_id=session_id, meta=meta, intent=intent)
            return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.providers.railway.service_creation_simulator.simulator_router import (
            route_railway_service_creation_simulator,
        )

        simulator_result = route_railway_service_creation_simulator(text, session_id=session_id)
        if simulator_result is not None:
            reply, intent, meta = simulator_result
            partial = ChatTurnResult(
                reply=reply,
                intent=intent,
                provider_stream=False,
                used_llm=False,
                meta={k: str(v) for k, v in meta.items()},
            )
            from aethos_core.chat.route_trace import save_last_route_trace as _save_sim_trace

            _save_sim_trace(session_id=session_id, meta=meta, intent=intent)
            return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.runtime_truth_alignment.runtime_truth_alignment_router import route_runtime_truth_alignment

        runtime_truth = route_runtime_truth_alignment(text, session_id=session_id)
        if runtime_truth is not None:
            reply, intent, meta = runtime_truth
            partial = ChatTurnResult(
                reply=reply,
                intent=intent,
                provider_stream=False,
                used_llm=False,
                meta={k: str(v) for k, v in meta.items()},
            )
            from aethos_core.chat.route_trace import save_last_route_trace as _save_rt_trace

            _save_rt_trace(session_id=session_id, meta=meta, intent=intent)
            return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.mission_control.mission_control_router import route_mission_control_observability

        mission_control_result = route_mission_control_observability(text, session_id=session_id)
        if mission_control_result is not None:
            reply, intent, meta = mission_control_result
            partial = ChatTurnResult(
                reply=reply,
                intent=intent,
                provider_stream=False,
                used_llm=False,
                meta={k: str(v) for k, v in meta.items()},
            )
            from aethos_core.chat.route_trace import save_last_route_trace as _save_mc_trace

            _save_mc_trace(session_id=session_id, meta=meta, intent=intent)
            return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.software_delivery.software_delivery_router import route_software_delivery

        software_delivery_result = route_software_delivery(text, session_id=session_id)
        if software_delivery_result is not None:
            reply, intent, meta = software_delivery_result
            partial = ChatTurnResult(
                reply=reply,
                intent=intent,
                provider_stream=False,
                used_llm=False,
                meta={k: str(v) for k, v in meta.items()},
            )
            from aethos_core.chat.route_trace import (
                save_last_route_trace as _save_sd_trace,
            )

            _save_sd_trace(session_id=session_id, meta=meta, intent=intent)
            return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.providers.railway.execution_contract.production_incident_command_router import (
            route_railway_production_incident_command,
        )

        incident_command_result = route_railway_production_incident_command(text, session_id=session_id)
        if incident_command_result is not None:
            reply, intent, meta = incident_command_result
            partial = ChatTurnResult(
                reply=reply,
                intent=intent,
                provider_stream=False,
                used_llm=False,
                meta={k: str(v) for k, v in meta.items()},
            )
            from aethos_core.chat.route_trace import (
                save_last_route_trace as _save_inc_trace,
            )

            _save_inc_trace(session_id=session_id, meta=meta, intent=intent)
            return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.providers.railway.execution_contract.production_canary_shadow_policy_router import (
            route_railway_production_canary_shadow_policy,
        )

        canary_shadow_policy_result = route_railway_production_canary_shadow_policy(
            text, session_id=session_id
        )
        if canary_shadow_policy_result is not None:
            reply, intent, meta = canary_shadow_policy_result
            partial = ChatTurnResult(
                reply=reply,
                intent=intent,
                provider_stream=False,
                used_llm=False,
                meta={k: str(v) for k, v in meta.items()},
            )
            from aethos_core.chat.route_trace import (
                save_last_route_trace as _save_csp_trace,
            )

            _save_csp_trace(session_id=session_id, meta=meta, intent=intent)
            return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.providers.railway.execution_contract.production_rollout_router import (
            route_railway_production_rollout,
        )

        production_rollout_result = route_railway_production_rollout(text, session_id=session_id)
        if production_rollout_result is not None:
            reply, intent, meta = production_rollout_result
            partial = ChatTurnResult(
                reply=reply,
                intent=intent,
                provider_stream=False,
                used_llm=False,
                meta={k: str(v) for k, v in meta.items()},
            )
            from aethos_core.chat.route_trace import (
                save_last_route_trace as _save_rollout_trace,
            )

            _save_rollout_trace(session_id=session_id, meta=meta, intent=intent)
            return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.providers.railway.execution_contract.production_rollback_escalation_router import (
            route_railway_production_rollback_escalation,
        )

        rollback_escalation_result = route_railway_production_rollback_escalation(
            text, session_id=session_id
        )
        if rollback_escalation_result is not None:
            reply, intent, meta = rollback_escalation_result
            partial = ChatTurnResult(
                reply=reply,
                intent=intent,
                provider_stream=False,
                used_llm=False,
                meta={k: str(v) for k, v in meta.items()},
            )
            from aethos_core.chat.route_trace import (
                save_last_route_trace as _save_esc_trace,
            )

            _save_esc_trace(session_id=session_id, meta=meta, intent=intent)
            return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.providers.railway.execution_contract.production_verification_router import (
            route_railway_production_verification,
        )

        production_verification_result = route_railway_production_verification(
            text, session_id=session_id
        )
        if production_verification_result is not None:
            reply, intent, meta = production_verification_result
            partial = ChatTurnResult(
                reply=reply,
                intent=intent,
                provider_stream=False,
                used_llm=False,
                meta={k: str(v) for k, v in meta.items()},
            )
            from aethos_core.chat.route_trace import (
                save_last_route_trace as _save_pv_trace,
            )

            _save_pv_trace(session_id=session_id, meta=meta, intent=intent)
            return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.providers.railway.execution_contract.production_shadow_router import (
            route_railway_production_shadow,
        )

        production_shadow_result = route_railway_production_shadow(text, session_id=session_id)
        if production_shadow_result is not None:
            reply, intent, meta = production_shadow_result
            partial = ChatTurnResult(
                reply=reply,
                intent=intent,
                provider_stream=False,
                used_llm=False,
                meta={k: str(v) for k, v in meta.items()},
            )
            from aethos_core.chat.route_trace import save_last_route_trace as _save_shadow_trace

            _save_shadow_trace(session_id=session_id, meta=meta, intent=intent)
            return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.providers.railway.execution_contract.execution_router import (
            route_railway_execution_contract,
        )

        execution_contract_result = route_railway_execution_contract(text, session_id=session_id)
        if execution_contract_result is not None:
            reply, intent, meta = execution_contract_result
            partial = ChatTurnResult(
                reply=reply,
                intent=intent,
                provider_stream=False,
                used_llm=False,
                meta={k: str(v) for k, v in meta.items()},
            )
            from aethos_core.chat.route_trace import save_last_route_trace as _save_exec_trace

            _save_exec_trace(session_id=session_id, meta=meta, intent=intent)
            return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.browser_observation.browser_observation_router import (
            is_browser_observation_lane_intent,
            route_browser_observation_lane,
        )

        if is_browser_observation_lane_intent(text):
            observation = route_browser_observation_lane(text, session_id=session_id)
            if observation is not None:
                reply, intent, meta = observation
                partial = ChatTurnResult(
                    reply=reply,
                    intent=intent,
                    provider_stream=False,
                    used_llm=False,
                    meta={k: str(v) for k, v in meta.items()},
                )
                from aethos_core.chat.route_trace import save_last_route_trace as _save_obs_trace

                _save_obs_trace(session_id=session_id, meta=meta, intent=intent)
                return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.providers.railway.deployment_readiness.deployment_readiness_intent import (
            is_railway_deployment_readiness_intent,
        )
        from aethos_core.providers.railway.deployment_readiness.deployment_readiness_safe_runtime import (
            safe_route_railway_deployment_readiness,
        )

        if is_railway_deployment_readiness_intent(text):
            readiness = safe_route_railway_deployment_readiness(text, session_id=session_id)
            if readiness is not None:
                reply, intent, meta = readiness
                partial = ChatTurnResult(
                    reply=reply,
                    intent=intent,
                    provider_stream=False,
                    used_llm=False,
                    meta={k: str(v) for k, v in meta.items()},
                )
                from aethos_core.chat.route_trace import save_last_route_trace as _save_railway_ready

                _save_railway_ready(session_id=session_id, meta=meta, intent=intent)
                return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.providers.github.workflow_lane.workflow_lane_router import (
            is_workflow_lane_intent,
            route_workflow_lane,
        )

        if is_workflow_lane_intent(text):
            lane_result = route_workflow_lane(text, session_id=session_id)
            if lane_result is not None:
                reply, intent, meta = lane_result
                partial = ChatTurnResult(
                    reply=reply,
                    intent=intent,
                    provider_stream=False,
                    used_llm=False,
                    meta={k: str(v) for k, v in meta.items()},
                )
                from aethos_core.chat.route_trace import save_last_route_trace as _save_lane_trace

                _save_lane_trace(session_id=session_id, meta=meta, intent=intent)
                return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        absolute = enforce_workflow_discovery_absolute_lane_turn(text, session_id=session_id)
        if absolute is not None:
            return safe_finalize_chat_result(absolute, context, emotional_context=emotional_context)

        from aethos_core.chat.route_trace import compose_internal_route_trace_reply

        internal = compose_internal_route_trace_reply(text, session_id=session_id)
        if internal is not None:
            reply, intent, meta = internal
            partial = ChatTurnResult(
                reply=reply,
                intent=intent,
                provider_stream=False,
                used_llm=False,
                meta=dict(meta),
            )
            return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
            route_workflow_discovery_hard_preemption_turn,
        )

        hard_workflow = route_workflow_discovery_hard_preemption_turn(text, session_id=session_id)
        if hard_workflow is not None:
            return safe_finalize_chat_result(hard_workflow, context, emotional_context=emotional_context)

        from aethos_core.post_mutation_verification.global_verification_preemption import (
            route_global_verification_query,
        )

        global_verification = route_global_verification_query(text, session_id=session_id)
        if global_verification is not None:
            return safe_finalize_chat_result(global_verification, context, emotional_context=emotional_context)

        from aethos_core.repair_memory.repair_outcome_router import route_repair_outcome_question

        repair_outcome = route_repair_outcome_question(text, session_id=session_id)
        if repair_outcome is not None:
            return safe_finalize_chat_result(repair_outcome, context, emotional_context=emotional_context)

        from aethos_core.providers.github.workflow_discovery.workflow_creation_plan import (
            route_workflow_creation_from_context,
        )

        creation_ctx = route_workflow_creation_from_context(text, session_id=session_id)
        if creation_ctx is not None:
            reply, intent, meta = creation_ctx
            partial = ChatTurnResult(
                reply=reply,
                intent=intent,
                provider_stream=False,
                used_llm=False,
                meta={k: str(v) for k, v in meta.items()},
            )
            from aethos_core.chat.route_trace import save_last_route_trace as _save_creation_trace

            _save_creation_trace(session_id=session_id, meta=meta, intent=intent)
            return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.providers.github.mutations.rerun_no_execution_followup import (
            compose_rerun_no_execution_followup,
        )

        no_exec = compose_rerun_no_execution_followup(text, session_id=session_id)
        if no_exec is not None:
            reply, intent, meta = no_exec
            partial = ChatTurnResult(
                reply=reply,
                intent=intent,
                provider_stream=False,
                used_llm=False,
                meta={k: str(v) for k, v in meta.items()},
            )
            from aethos_core.chat.route_trace import save_last_route_trace

            trace_meta = dict(meta)
            trace_meta["workflow_discovery_delegation_executed"] = trace_meta.get("workflow_discovery_delegated", "")
            save_last_route_trace(session_id=session_id, meta=trace_meta, intent=intent)
            return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
            route_workflow_discovery_followup,
        )

        workflow_discovery = route_workflow_discovery_followup(text, session_id=session_id)
        if workflow_discovery is not None:
            reply, intent, meta = workflow_discovery
            partial = ChatTurnResult(
                reply=reply,
                intent=intent,
                provider_stream=False,
                used_llm=False,
                meta={k: str(v) for k, v in meta.items()},
            )
            from aethos_core.chat.route_trace import save_last_route_trace as _save_trace

            _save_trace(session_id=session_id, meta=meta, intent=intent)
            return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.world_model.investigation_strategy_router import route_investigation_strategy_question

        strategy = route_investigation_strategy_question(text, session_id=session_id)
        if strategy is not None:
            return safe_finalize_chat_result(strategy, context, emotional_context=emotional_context)

        from aethos_core.devops_intent_planner.devops_capability_router import route_devops_capability_question

        devops_capability = route_devops_capability_question(text, session_id=session_id)
        if devops_capability is not None:
            return safe_finalize_chat_result(devops_capability, context, emotional_context=emotional_context)

        from aethos_core.provider_readonly_intent.readonly_provider_router import route_readonly_provider_question

        readonly_provider = route_readonly_provider_question(text, session_id=session_id)
        if readonly_provider is not None:
            return safe_finalize_chat_result(readonly_provider, context, emotional_context=emotional_context)

        from aethos_core.chat.informational_help_router import route_informational_help_turn

        informational_help = route_informational_help_turn(text, session_id=session_id, channel=channel)
        if informational_help is not None:
            return safe_finalize_chat_result(informational_help, context, emotional_context=emotional_context)

        from aethos_core.chat.front_door_router import compose_front_door_route_reply

        front_door = compose_front_door_route_reply(text, session_id=session_id)
        if front_door is not None:
            reply, intent, meta = front_door
            partial = ChatTurnResult(
                reply=reply,
                intent=intent,
                provider_stream=False,
                used_llm=False,
                meta=dict(meta),
            )
            return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)

        from aethos_core.chat.operational_master_router import resolve_operational_master_route

        master = resolve_operational_master_route(text, session_id=session_id, channel=channel)
        if master is None:
            return None
        partial = ChatTurnResult(
            reply=master.reply,
            intent=master.intent,
            provider_stream=False,
            used_llm=False,
            meta=dict(master.meta),
        )
        safe_record_route_trace(session_id=session_id, decision=master)
        return safe_finalize_chat_result(partial, context, emotional_context=emotional_context)
    except Exception as exc:
        _log.exception(
            "Operational cognition boundary caught error session=%s channel=%s text=%r",
            session_id,
            channel,
            (text or "")[:160],
        )
        return compose_cognition_crash_fallback(exc, context, partial_result=partial)


def safe_finalize_chat_result(
    result: ChatTurnResult,
    context: CognitionBoundaryContext,
    *,
    emotional_context: dict[str, object] | None = None,
) -> ChatTurnResult:
    """Finalize/polish a chat result without failing the transport."""
    try:
        from aethos_core.chat.service import _finalize_result

        finalized = _finalize_result(result, emotional_context=emotional_context)
        return sanitize_chat_result_for_transport(finalized)
    except Exception as exc:
        _log.exception(
            "Chat finalization failed session=%s intent=%s",
            context.session_id,
            result.intent,
        )
        fallback = compose_cognition_crash_fallback(
            exc,
            context,
            partial_result=result,
            stage="finalization",
        )
        return sanitize_chat_result_for_transport(fallback)


def _is_genuine_world_model_recall(text: str, session_id: str) -> bool:
    """True only for a genuine world-model recall (safety / follow-up / active investigation).

    Stops the crash fallback from dressing an unrelated fresh request — most
    importantly a multi-agent command-center / orchestration ask — up as a
    "recalled investigation". Such requests get an honest generic error instead.
    """
    try:
        from aethos_core.agents.runtime.planner import is_command_center_orchestration_request

        if is_command_center_orchestration_request(text, session_id=session_id):
            return False
    except Exception:
        pass
    try:
        from aethos_core.world_model.safety_question_classifier import is_safety_question

        if is_safety_question(text):
            return True
        from aethos_core.world_model.world_model_followup_router import classify_world_model_followup

        if classify_world_model_followup(text, session_id=session_id) is not None:
            return True
        from aethos_core.world_model.world_state_store import get_active_investigation

        return get_active_investigation(session_id=session_id) is not None
    except Exception:
        return False


def compose_cognition_crash_fallback(
    error: BaseException | str,
    context: CognitionBoundaryContext,
    *,
    partial_result: ChatTurnResult | None = None,
    stage: str = "cognition_route",
) -> ChatTurnResult:
    """Bounded fallback when cognition delivery fails."""
    from aethos_core.providers.railway.greenfield_deployment.greenfield_router import (
        preemption_chat_turn_result,
    )

    greenfield = preemption_chat_turn_result(
        context.text,
        session_id=context.session_id,
        route_source="cognition_crash_greenfield_preemption",
    )
    if greenfield is not None:
        return greenfield

    from aethos_core.chat.front_door_intent import (
        classify_front_door_intent,
        compose_front_door_reply,
        should_skip_operational_cognition,
    )

    front_door_intent = classify_front_door_intent(context.text)
    if should_skip_operational_cognition(context.text, intent=front_door_intent):
        front_door = compose_front_door_reply(
            front_door_intent,
            text=context.text,
            session_id=context.session_id,
        )
        if front_door is not None:
            reply, intent, meta = front_door
            return ChatTurnResult(
                reply=reply,
                intent=intent,
                provider_stream=False,
                used_llm=False,
                meta={k: str(v) for k, v in meta.items()},
            )

    from aethos_core.chat.job_result_followup_router import compose_job_result_followup_reply

    job_followup = compose_job_result_followup_reply(context.text, session_id=context.session_id)
    if job_followup is not None:
        reply, intent, meta = job_followup
        return ChatTurnResult(
            reply=reply,
            intent=intent,
            provider_stream=False,
            used_llm=False,
            meta={k: str(v) for k, v in meta.items()},
        )

    diagnostic_id = f"cogerr-{uuid.uuid4().hex[:8]}"
    error_type = type(error).__name__ if isinstance(error, BaseException) else "CognitionError"
    from aethos_core.world_model.fallback_context_resolver import resolve_fallback_context
    from aethos_core.world_model.safety_question_classifier import is_safety_question

    fallback = resolve_fallback_context(text=context.text, session_id=context.session_id)
    followup_kind = _world_model_kind_from_text(context.text)
    service = fallback.service if fallback else ""
    target = fallback.target if fallback else ""
    project = fallback.project if fallback else ""
    status = fallback.status if fallback else "failed"
    evidence = fallback.evidence_summary if fallback else ""
    recommendation = (
        fallback.recommendation
        if fallback and fallback.recommendation
        else "Refresh Railway service events and fetch logs around the latest failed deployment window."
    )

    genuine_world_model = _is_genuine_world_model_recall(context.text, context.session_id)
    used_world_model_framing = False

    if partial_result is not None and (partial_result.reply or "").strip() and not is_safety_question(context.text):
        reply = partial_result.reply.strip()
        if diagnostic_id not in reply:
            reply = f"{reply}\n\nDiagnostic ID: {diagnostic_id}"
    elif is_safety_question(context.text) and fallback and fallback.has_target():
        reply = _compose_safety_crash_fallback(
            service=service,
            recommendation=recommendation,
            evidence_summary=evidence,
            diagnostic_id=diagnostic_id,
        )
        used_world_model_framing = True
    elif fallback and fallback.has_target() and genuine_world_model:
        opener = f"I hit an internal error while recalling the **{service}** investigation"
        if project:
            opener += f" in **{project}**"
        opener += ", but I recovered enough context to continue."
        lines = [
            opener,
            "",
            "Reliable context:",
            f"- Target: **{target}**",
            f"- Current state: **{status}**",
            f"- Recent evidence: **{evidence or 'fresh WiredTiger logs, stale service events'}**",
            f"- Current recommendation: {recommendation}",
            "",
            "No mutation has been performed.",
            "",
            f"Diagnostic ID: {diagnostic_id}",
        ]
        reply = "\n".join(lines)
        used_world_model_framing = True
    else:
        # Honest, un-masked error for a fresh request that is *not* a world-model
        # recall (e.g. an orchestration ask that crashed upstream). Do not pretend
        # we "recovered investigation context" we never had.
        reply = (
            "I hit an internal error handling this request and stopped safely before taking any action.\n\n"
            "No mutation has been performed. Please try again — if it keeps happening, share this diagnostic id.\n\n"
            f"Diagnostic ID: {diagnostic_id}"
        )

    badge_world_model = used_world_model_framing or partial_result is not None
    intent = partial_result.intent if partial_result is not None else _intent_from_text(context.text)
    meta: dict[str, object] = {
        "route_id": "world_model_investigation" if badge_world_model else "cognition_exception_fallback",
        "matched_module": (
            "world_model.fallback_context_resolver" if badge_world_model else "chat.cognition_exception_boundary"
        ),
        "cognition_boundary": "true",
        "cognition_error_type": error_type,
        "cognition_error_stage": stage,
        "cognition_diagnostic_id": diagnostic_id,
        "recovered": "true",
        "fallback_used": "cognition_crash_fallback",
        "blocked_routes": "operation_preflight,explicit_mutation,continuity_reconstruction,generic_fix_plan",
    }
    if badge_world_model:
        meta["world_model_degraded"] = "true"
    if fallback and badge_world_model:
        meta.update(_sanitize_value(fallback.to_dict()))
        meta["matched_target"] = target
        if service:
            meta["service"] = service
        if project:
            meta["project"] = project
    if partial_result is not None:
        meta.update(_sanitize_value(dict(partial_result.meta or {})))
    if followup_kind and badge_world_model:
        meta["world_model_intent"] = followup_kind
        meta["route_trace"] = f"world_model_investigation → {followup_kind}"
    if badge_world_model:
        save_world_model_fallback_route_trace(
            session_id=context.session_id,
            intent=intent,
            meta=meta,
            matched_target=target,
            followup_kind=followup_kind,
        )
    return ChatTurnResult(
        reply=reply,
        intent=intent,
        provider_stream=False,
        used_llm=False,
        meta=meta,
    )


def save_world_model_fallback_route_trace(
    *,
    session_id: str,
    intent: str,
    meta: dict[str, object],
    matched_target: str = "",
    followup_kind: str = "",
) -> None:
    try:
        from aethos_core.chat.route_trace import save_last_route_trace

        trace_meta = {str(k): str(v) for k, v in meta.items()}
        trace_meta["route_id"] = "world_model_investigation"
        trace_meta["matched_module"] = "world_model.fallback_context_resolver"
        trace_meta["matched_target"] = matched_target or trace_meta.get("target", "")
        trace_meta["fallback_used"] = "cognition_crash_fallback"
        trace_meta["recovered"] = "true"
        if followup_kind:
            trace_meta["world_model_intent"] = followup_kind
            trace_meta["route_trace"] = f"world_model_investigation → {followup_kind}"
        save_last_route_trace(session_id=session_id, meta=trace_meta, intent=intent)
    except Exception:
        _log.exception("World-model fallback route trace persistence failed session=%s", session_id)


def _compose_safety_crash_fallback(
    *,
    service: str,
    recommendation: str,
    evidence_summary: str,
    diagnostic_id: str,
) -> str:
    lines = [
        "Not yet.",
        "",
        f"Restart is not recommended for **{service}** right now because the root cause is still unconfirmed.",
        "",
        "Evidence:",
        f"- **{service}** is failed.",
    ]
    low = (evidence_summary or "").lower()
    if "wiredtiger" in low:
        lines.append("- Logs only show WiredTiger startup/storage activity.")
    if "stale service events" in low:
        lines.append("- Service events are stale.")
    lines.append("- No fatal error or exit reason is confirmed.")
    lines.extend(
        [
            "",
            "Safer next step:",
            recommendation,
            "",
            "No mutation has been performed.",
            "",
            f"Diagnostic ID: {diagnostic_id}",
        ]
    )
    return "\n".join(lines)


def _world_model_kind_from_text(text: str) -> str:
    from aethos_core.world_model.safety_question_classifier import is_safety_question
    from aethos_core.world_model.world_model_followup_router import classify_world_model_followup

    if is_safety_question(text):
        return "safety_check"
    kind = classify_world_model_followup(text)
    return kind or "recap"


def safe_record_route_trace(*, session_id: str, decision: Any) -> None:
    try:
        from aethos_core.chat.operational_master_router import record_master_route_trace

        record_master_route_trace(session_id=session_id, decision=decision)
    except Exception:
        _log.exception("Route trace persistence failed session=%s", session_id)


def sanitize_chat_result_for_transport(result: ChatTurnResult) -> ChatTurnResult:
    """Ensure chat results are JSON-serializable for API/Telegram transports."""
    meta = _sanitize_value(dict(result.meta or {}))
    if not isinstance(meta, dict):
        meta = {"meta": meta}
    return ChatTurnResult(
        reply=str(result.reply or ""),
        intent=str(result.intent or ""),
        agent_key=str(result.agent_key or "aethos"),
        terminal=bool(result.terminal),
        provider_stream=bool(result.provider_stream),
        used_llm=bool(result.used_llm),
        provider=str(result.provider) if result.provider is not None else None,
        model=str(result.model) if result.model is not None else None,
        meta=meta,
    )


def _intent_from_text(text: str) -> str:
    try:
        from aethos_core.world_model.world_model_followup_router import classify_world_model_followup

        intent = classify_world_model_followup(text)
        mapping = {
            "recap": "world_model_investigation_recap",
            "next_step": "world_model_next_action",
            "safety_check": "world_model_restart_safety",
            "evidence_delta": "world_model_what_changed",
            "hypothesis_summary": "world_model_hypothesis_summary",
            "missing_evidence": "world_model_missing_evidence",
            "blocker_summary": "world_model_blocker_summary",
            "investigation_status": "world_model_investigation_status",
        }
        if intent is not None:
            return mapping.get(intent, "world_model_investigation_recap")
    except Exception:
        pass
    return "cognition_exception_fallback"


def _sanitize_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, BaseException):
        return f"{type(value).__name__}: {value}"
    if is_dataclass(value):
        return _sanitize_value(asdict(value))
    if isinstance(value, dict):
        return {str(key): _sanitize_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_sanitize_value(item) for item in value]
    return str(value)
