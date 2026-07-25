# SPDX-License-Identifier: Apache-2.0
"""DevOps capability router — truthful capability answers and plan-first DevOps workflows."""

from __future__ import annotations

from aethos_core.capability_truth.capability_truth_composer import (
    compose_capability_truth_reply,
    compose_unimplemented_provider_gap,
)
from aethos_core.chat.service import ChatTurnResult
from aethos_core.devops_intent_planner.devops_request_classifier import (
    classify_devops_request,
    detect_requested_providers,
    is_capability_truth_question,
    is_end_to_end_devops_request,
)
from aethos_core.devops_intent_planner.end_to_end_plan_builder import compose_end_to_end_plan_reply


def devops_capability_preemption_blocks_route(text: str, *, session_id: str = "default") -> bool:
    return classify_devops_request(text, session_id=session_id) in {"capability_truth", "end_to_end_plan"}


def compose_devops_capability_route_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    kind = classify_devops_request(text, session_id=session_id)
    if kind == "none":
        return None

    if kind == "capability_truth":
        from aethos_core.identity.plain_capability_intro import (
            compose_plain_capability_overview_reply,
            compose_provider_connection_status_reply,
            is_provider_connection_question,
        )
        from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_intent import (
            is_general_capability_question,
        )

        if is_provider_connection_question(text):
            reply = compose_provider_connection_status_reply(session_id=session_id)
        elif is_general_capability_question(text):
            reply = compose_plain_capability_overview_reply(session_id=session_id)
        else:
            reply = compose_capability_truth_reply(text)
            meta = {
                "route_id": "devops_capability",
                "matched_module": "devops_intent_planner.devops_capability_router",
                "devops_request_kind": "capability_truth",
                "suppress_governance_footer": "true",
            }
            return reply, "capability_truth", meta

        meta = {
            "route_id": "capability_registry_runtime_integration",
            "matched_module": (
                "mission_control.capability_registry_runtime_integration."
                "capability_registry_runtime_integration_service"
            ),
            "devops_request_kind": "capability_truth",
            "runtime_answer_from_fix_295": "true",
            "suppress_governance_footer": "true",
        }
        return reply, "mission_control_capability_registry_runtime_integration", meta

    if kind == "end_to_end_plan":
        from aethos_core.chat.provider_deploy_capability_intent import route_provider_deploy_capability_reply

        provider_truth = route_provider_deploy_capability_reply(text, session_id=session_id)
        if provider_truth is not None:
            return provider_truth

        providers = detect_requested_providers(text)
        unimplemented = [
            provider
            for provider in providers
            if provider in {"aws", "gcp", "azure", "kubernetes"}
        ]
        if len(unimplemented) == 1 and count_single_provider_end_to_end(text, provider=unimplemented[0]):
            reply = compose_unimplemented_provider_gap(unimplemented[0])
            return reply, "provider_capability_gap", {
                "route_id": "devops_capability",
                "matched_module": "devops_intent_planner.devops_capability_router",
                "devops_request_kind": "provider_capability_gap",
                "provider": unimplemented[0],
            }

        reply = compose_end_to_end_plan_reply(text, session_id=session_id)
        return reply, "devops_end_to_end_plan", {
            "route_id": "devops_capability",
            "matched_module": "devops_intent_planner.devops_capability_router",
            "devops_request_kind": "end_to_end_plan",
        }

    return None


def route_devops_capability_question(
    text: str,
    *,
    session_id: str = "default",
) -> ChatTurnResult | None:
    routed = compose_devops_capability_route_reply(text, session_id=session_id)
    if routed is None:
        return None
    reply, intent, meta = routed
    return ChatTurnResult(
        reply=reply,
        intent=intent,
        provider_stream=False,
        used_llm=False,
        meta=dict(meta),
    )


def count_single_provider_end_to_end(text: str, *, provider: str) -> bool:
    providers = detect_requested_providers(text)
    return len(providers) == 1 and providers[0] == provider and is_end_to_end_devops_request(text)
