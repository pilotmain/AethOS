# SPDX-License-Identifier: Apache-2.0
"""Relational runtime — orchestrate emotional intelligence layer."""

from __future__ import annotations

from typing import Any

from aethos_core.relational.conversational_memory import append_turn, recent_context
from aethos_core.relational.emotional_context import build_emotional_context
from aethos_core.relational.warmth_engine import apply_warmth, reduce_verbosity


def prepare_relational_turn(
    *,
    user_text: str,
    session_id: str = "default",
    channel: str = "chat",
) -> dict[str, Any]:
    """Prepare relational context before orchestration."""
    operational_context = None
    try:
        from aethos_core.reliability.reliability_runtime import assess_operational_reliability

        rel = assess_operational_reliability()
        operational_context = rel.get("reliability") or {}
    except Exception:
        pass

    ctx = build_emotional_context(
        user_text=user_text,
        session_id=session_id,
        channel=channel,
        operational_context=operational_context,
    )
    ctx["recent_turns"] = recent_context(session_id=session_id)
    ctx["session_id"] = session_id
    ctx["channel"] = channel
    try:
        from aethos_core.conversation.polish_compat import enrich_emotional_context

        ctx = enrich_emotional_context(ctx, user_text=user_text, session_id=session_id, channel=channel)
    except Exception:
        pass
    append_turn(session_id=session_id, role="user", summary=user_text[:200])
    return ctx


def finalize_relational_reply(
    reply: str,
    *,
    emotional_context: dict[str, Any],
    intent: str = "generative_answer",
    lane: str | None = None,
    suppress_governance_footer: bool = False,
) -> tuple[str, dict[str, str]]:
    """Apply warmth and record assistant turn."""
    from aethos_core.relational.presence_timing import build_response_timing

    mode = (emotional_context.get("mode") or {}).get("mode") or "companion"
    from aethos_core.providers.railway.deployment_plan.deployment_plan_presentation import (
        is_railway_deployment_plan_presentation_bypass,
    )

    if is_railway_deployment_plan_presentation_bypass(intent=intent):
        append_turn(session_id=emotional_context.get("session_id", "default"), role="assistant", summary=reply[:200])
        timing = build_response_timing(intent=intent)
        return reply, {
            "relational_mode": str((emotional_context.get("mode") or {}).get("mode") or "companion"),
            "human_signals": ",".join((emotional_context.get("signals") or {}).get("signals") or []),
            "autonomous_execution_blocked": "true",
            "lane": lane or "human_centered",
            "response_timing": str(timing.get("adaptive_typing_cadence_ms", 80)),
        }

    shaped = reply
    if intent not in {
        "mutation_target_blocked",
        "mutation_target_update",
        "mutation_target_clarification",
        "job_approval_guidance",
        "mutation_execution_truth",
    } and (
        mode in ("crisis", "executive", "operator")
        or (emotional_context.get("signals") or {}).get("frustrated")
    ):
        shaped = reduce_verbosity(shaped)
    grounding = emotional_context.get("operational_grounding") or {}
    suppress_governance = bool(
        suppress_governance_footer
        or grounding.get("grounded")
        or (grounding.get("continuity_intent") or {}).get("continuity_prompt")
        or lane == "operational_entity"
        or lane == "operational_progression"
    )
    shaped = apply_warmth(
        shaped,
        emotional_context=emotional_context,
        intent=intent,
        lane=lane,
        include_governance_footer=not suppress_governance,
    )
    append_turn(session_id=emotional_context.get("session_id", "default"), role="assistant", summary=shaped[:200])
    timing = build_response_timing(intent=intent)
    meta = {
        "relational_mode": mode,
        "human_signals": ",".join((emotional_context.get("signals") or {}).get("signals") or []),
        "autonomous_execution_blocked": "true",
        "lane": lane or "human_centered",
        "response_timing": str(timing.get("adaptive_typing_cadence_ms", 80)),
    }
    return shaped, meta


def get_relational_state(*, session_id: str = "default") -> dict[str, Any]:
    ctx = build_emotional_context(user_text="", session_id=session_id)
    return {
        "ok": True,
        "emotional_context": ctx,
        "recent_turns": recent_context(session_id=session_id),
        "autonomous_execution_blocked": True,
    }
