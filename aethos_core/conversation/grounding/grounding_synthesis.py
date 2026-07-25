# SPDX-License-Identifier: Apache-2.0
"""Grounding synthesis — operational-state-aware conversational synthesis."""

from __future__ import annotations

from typing import Any

from aethos_core.continuity_reconstruction.prompt_inference import infer_continuity_intent
from aethos_core.continuity_reconstruction.thread_recovery import reconstruct_operational_thread
from aethos_core.conversation.realism.anti_generic import reshape_generic_response
from aethos_core.conversation.realism.conversational_pacing import (
    brief_low_confidence_reply,
    decisive_uncertainty_lead,
    pacing_profile,
)
from aethos_core.conversation.realism.interaction_shaping import shape_interaction
from aethos_core.conversation.realism.narrative_diversification import (
    diversify_monitoring_close,
    diversify_stability_opening,
    uncertain_continuity_prefix,
)
from aethos_core.conversation.realism.semantic_diversification import (
    compose_improvement_narrative,
    compose_monitoring_narrative,
    compose_stability_narrative,
)
from aethos_core.conversation.realism.thread_resurrection_guard import assess_thread_resurrection
from aethos_core.live_operational_grounding.live_narrative_composer import compose_live_stability_reply
from aethos_core.live_operational_grounding.live_reality_convergence import assess_live_reality_convergence
from aethos_core.live_operational_grounding.regression_guardrails import assess_regression_guardrails
from aethos_core.operational_partner_presence.partner_runtime import build_partner_context

_LOW_CONFIDENCE = 0.52


def _uncertainty_lead(
    thread: dict[str, Any],
    *,
    session_id: str,
    confidence: float,
    pacing: dict[str, Any],
) -> str:
    subject = thread.get("primary_subject") or "the earlier operational thread"
    if thread.get("certainty_tier") == "low":
        return ""
    if (thread.get("ambiguity") or {}).get("ambiguous") and pacing.get("mode") == "decisive":
        return decisive_uncertainty_lead(subject=str(subject))
    if (thread.get("ambiguity") or {}).get("ambiguous") and confidence >= _LOW_CONFIDENCE:
        return uncertain_continuity_prefix(subject=str(subject), session_id=session_id) + "\n\n"
    return ""


def synthesize_grounded_operational_reply(
    *,
    user_text: str,
    session_id: str = "default",
    channel: str = "chat",
) -> dict[str, Any] | None:
    intent_info = infer_continuity_intent(user_text)
    if not intent_info.get("continuity_prompt"):
        return None

    thread = reconstruct_operational_thread(session_id=session_id, channel=channel, user_text=user_text)
    partner = build_partner_context(session_id=session_id, channel=channel)
    intent = str(intent_info.get("intent") or "implicit_followup")
    confidence = float(thread.get("continuity_confidence") or 0.0)
    certainty_tier = str(thread.get("certainty_tier") or "moderate")
    pacing = pacing_profile(confidence=confidence, channel=channel, certainty_tier=certainty_tier)

    decay = thread.get("continuity_decay") or {}
    selection = thread.get("subject_selection") or {}
    resurrection = assess_thread_resurrection(
        subject=str(thread.get("primary_subject") or ""),
        category=str(selection.get("category") or "recovery"),
        bridge=thread,
        age_hours=float(decay.get("age_hours") or 0.0),
    )
    if resurrection.get("resurrection_risk"):
        confidence = max(0.3, confidence - float(resurrection.get("confidence_penalty") or 0.0))

    subject = thread.get("primary_subject") or "the active operational thread"
    category = selection.get("category") or "recovery"
    live = assess_live_reality_convergence(
        session_id=session_id,
        channel=channel,
        primary_subject=str(subject),
        category=str(category),
    )
    from aethos_core.live_operational_grounding.recovery_verification_windows import assess_recovery_verification_windows

    live["verification_windows"] = assess_recovery_verification_windows(
        session_id=session_id,
        provider_converged=bool((live.get("provider_binding") or {}).get("provider_truth", {}).get("converged")),
    )
    if live.get("contradictory_surfaces"):
        confidence = max(0.3, confidence - 0.1)
    if live.get("freshness", {}).get("stale"):
        confidence = max(0.3, confidence - 0.08)

    lead = _uncertainty_lead(thread, session_id=session_id, confidence=confidence, pacing=pacing)
    closing = diversify_monitoring_close(session_id=session_id)
    opening = diversify_stability_opening(session_id=session_id)

    replay = thread.get("replay_concern") or "replay continuity"
    topology = thread.get("topology_concern") or "topology endurance"
    live_binding = live.get("provider_binding") or {}
    runtime_signals = live_binding.get("runtime_signals") or thread.get("runtime_signals") or {}

    if confidence < _LOW_CONFIDENCE and intent in {"implicit_followup", "situation_improved", "what_changed"}:
        alts = (thread.get("ambiguity") or {}).get("alternatives") or []
        alt = alts[0]["subject"] if alts else None
        reply = brief_low_confidence_reply(alt_subject=str(alt) if alt else None)
    elif intent in {"deployment_stabilized", "recovery_status", "did_it_hold"}:
        reply = compose_live_stability_reply(
            subject=str(subject),
            live=live,
            closing=closing,
            intent=intent,
        )
        if lead and "mismatch" not in reply.lower():
            reply = f"{lead}{reply}"
    elif intent == "situation_improved":
        concern = replay if category == "replay" else topology if category == "topology" else subject
        signals = [
            runtime_signals.get("summary") or "telemetry staying fresh",
            "dependency responses stable",
            "no new erosion acceleration",
        ]
        body = compose_improvement_narrative(
            concern=str(concern),
            signals=[str(s) for s in signals[:3]],
            closing=closing,
            session_id=session_id,
        )
        reply = f"{lead}{body}"
    elif intent == "monitoring_advice":
        if live.get("live_converged"):
            reply = compose_live_stability_reply(
                subject=str(replay if category == "replay" else topology if category == "topology" else subject),
                live=live,
                closing="",
                intent="monitoring_advice",
            )
        else:
            sensitive = replay if category == "replay" else topology if category == "topology" else subject
            reply = f"{lead}{compose_monitoring_narrative(sensitive=str(sensitive), session_id=session_id)}"
    elif intent == "what_changed":
        narrative = runtime_signals.get("summary") or f"focus remained on {subject}"
        reply = compose_live_stability_reply(
            subject=str(subject),
            live=live,
            closing=closing,
            intent="what_changed",
        )
        if narrative not in reply:
            reply = f"{lead}Since our last thread, {narrative}\n\n{closing}"
    else:
        reply = (
            f"{lead}Based on **{subject}**, {opening.lower()}\n\n"
            f"Recovery signals look healthy from here. {closing}"
        )

    reply = reshape_generic_response(reply, context=thread, intent=intent)
    reply = shape_interaction(reply, channel=channel, pacing=pacing)
    guardrails = assess_regression_guardrails(reply=reply, grounded=True)

    return {
        "reply": reply,
        "intent": intent,
        "grounded": True,
        "continuity_confidence": round(confidence, 2),
        "certainty_tier": certainty_tier,
        "pacing": pacing,
        "resurrection_guard": resurrection,
        "live_grounding": live,
        "regression_guardrails": guardrails,
        "ambiguity": thread.get("ambiguity"),
        "subject_selection": selection,
        "partner_context": partner,
        "summary": "Live operational grounding synthesis complete.",
    }
