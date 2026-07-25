# SPDX-License-Identifier: Apache-2.0
"""Chat grounding — conversational pipeline integration."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.grounding.grounding_runtime import prepare_grounding_context
from aethos_core.conversation.grounding.grounding_synthesis import synthesize_grounded_operational_reply
from aethos_core.conversation.realism.anti_generic import is_generic_ai_response, reshape_generic_response
from aethos_core.governance_restraint_runtime.restraint_runtime import apply_governance_restraint
from aethos_core.telegram_session_persistence.session_bridge import persist_telegram_continuity


def enrich_emotional_context(
    emotional_context: dict[str, Any],
    *,
    user_text: str,
    session_id: str,
    channel: str,
) -> dict[str, Any]:
    grounding = prepare_grounding_context(user_text=user_text, session_id=session_id, channel=channel)
    emotional_context["operational_grounding"] = grounding
    emotional_context["session_id"] = session_id
    emotional_context["channel"] = channel
    try:
        from aethos_core.conversation.grounding.entity_grounding import enrich_operational_entity_context

        emotional_context = enrich_operational_entity_context(
            emotional_context,
            session_id=session_id,
            channel=channel,
        )
    except Exception:
        pass
    return emotional_context


def try_grounded_chat_reply(
    user_text: str,
    *,
    session_id: str = "default",
    channel: str = "chat",
) -> tuple[str, str, dict[str, str]] | None:
    synthesized = synthesize_grounded_operational_reply(
        user_text=user_text,
        session_id=session_id,
        channel=channel,
    )
    if synthesized is None:
        return None
    meta = {
        "lane": "operational_grounding",
        "grounded": "true",
        "continuity_confidence": str(synthesized.get("continuity_confidence") or ""),
    }
    return synthesized["reply"], str(synthesized.get("intent") or "operational_grounding"), meta


def finalize_grounded_reply(
    reply: str,
    *,
    emotional_context: dict[str, Any] | None,
    intent: str,
    lane: str | None = None,
    suppress_governance_footer: bool = False,
) -> str:
    from aethos_core.providers.railway.deployment_plan.deployment_plan_presentation import (
        is_railway_deployment_plan_presentation_bypass,
    )

    if is_railway_deployment_plan_presentation_bypass(intent=intent):
        return reply

    ctx = emotional_context or {}
    grounding = ctx.get("operational_grounding") or {}
    bridge = grounding.get("operational_context") or {}
    channel = str(ctx.get("channel") or "chat")

    if is_generic_ai_response(reply):
        reply = reshape_generic_response(
            reply,
            context=bridge,
            intent=intent,
        )

    reply = apply_governance_restraint(
        reply,
        intent=intent,
        lane=lane,
        channel=channel,
        emotional_context=ctx,
        grounded=True,
        suppress_governance_footer=suppress_governance_footer,
    )

    from aethos_core.conversation.realism.interaction_shaping import shape_interaction
    from aethos_core.conversation.realism.conversational_pacing import pacing_profile

    confidence = 0.6
    try:
        confidence = float((grounding.get("continuity_intent") or {}).get("confidence") or 0.6)
    except (TypeError, ValueError):
        pass
    pacing = pacing_profile(confidence=confidence, channel=channel)
    if lane in {"operational_progression", "operational_entity"} or intent in {
        "mutation_target_blocked",
        "mutation_target_update",
        "mutation_target_clarification",
        "job_approval_guidance",
        "mutation_execution_truth",
        "railway_named_service_logs",
        "multi_provider_health_report",
    }:
        pacing = {**pacing, "compress": False}
    reply = shape_interaction(reply, channel=channel, pacing=pacing)

    focus = bridge.get("primary_subject")
    if focus:
        persist_telegram_continuity(
            session_id=str(ctx.get("session_id") or "default"),
            focus=str(focus),
            investigation=(bridge.get("active_investigations") or [None])[0],
            context={
                "latest_recovery_narrative": reply[:240],
                "runtime_signals": bridge.get("runtime_signals") or {},
            },
        )
    return reply
