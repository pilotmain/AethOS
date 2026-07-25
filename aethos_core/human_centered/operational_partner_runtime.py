# SPDX-License-Identifier: Apache-2.0
"""Operational partner runtime — Phase 10.1.4 companion intelligence orchestrator."""

from __future__ import annotations

from time import time
from typing import Any


def render_operational_partner_brief(*, session_id: str = "default", user_text: str | None = None) -> dict[str, Any]:
    """Slice J — operational partner threshold end-state."""
    from aethos_core.attention.attention_awareness import assess_operator_attention
    from aethos_core.collaboration.investigation.investigation_companion import build_investigation_companion_brief
    from aethos_core.conversation.flow.conversation_flow import apply_conversation_flow
    from aethos_core.human_centered.continuity_memory import load_continuity_memory, seed_default_continuity
    from aethos_core.intuition.companion_quality_metrics import compute_companion_quality_metrics
    from aethos_core.narrative.companion_narrative import build_companion_narrative
    from aethos_core.presence.emotional_realism.emotional_realism_runtime import assess_emotional_realism
    from aethos_core.reasoning.reasoning_engine import assess_deep_operational_reasoning
    from aethos_core.replay.deep_replay.deep_replay_runtime import get_deep_replay_intelligence
    from aethos_core.restraint.restraint_v2 import apply_restraint_v2

    seed_default_continuity(session_id=session_id)
    record = load_continuity_memory(session_id=session_id)
    reasoning = assess_deep_operational_reasoning(session_id=session_id)
    investigation = build_investigation_companion_brief(session_id=session_id)
    replay = get_deep_replay_intelligence(session_id=session_id)
    emotional = assess_emotional_realism(session_id=session_id, user_text=user_text)
    attention = assess_operator_attention(session_id=session_id)
    narrative = build_companion_narrative(session_id=session_id)
    quality = compute_companion_quality_metrics(session_id=session_id)

    confidence = float(record.get("confidence") or 0.82)
    unresolved = (record.get("unresolved") or ["replay continuity during long-running scheduler cycles"])[0]

    core_parts = [
        emotional.get("tone_narrative", ""),
        investigation.get("narrative", ""),
        reasoning.get("synthesis", ""),
        f"I don't think this is production-critical yet.",
        "",
        f"The next best step is validating replay consistency across extended operational sessions "
        f"before introducing deeper ambient presence behaviors.",
    ]

    if attention.get("narrative"):
        core_parts.insert(0, attention.get("narrative", ""))

    core = "\n\n".join(p for p in core_parts if p and str(p).strip())
    restrained = apply_restraint_v2(
        text=core,
        session_id=session_id,
        confidence=confidence,
        suggestion_count=len(replay.get("investigation_branches") or []),
    )
    flowed = apply_conversation_flow(
        session_id=session_id,
        core_text=restrained.get("text", core),
        confidence=confidence,
        verbosity="high",
    )

    return {
        "ok": True,
        "phase": "10.1.4",
        "identity": "operational partner",
        "principle": "extraordinarily capable operational partner that helps people think more clearly",
        "brief": flowed,
        "brief_core": core,
        "operational_reasoning": reasoning,
        "investigation_companion": investigation,
        "deep_replay": replay,
        "emotional_realism": emotional,
        "attention_awareness": attention,
        "companion_narrative": narrative,
        "companion_quality": quality,
        "remaining_risk": unresolved,
        "confidence": confidence,
        "restraint": restrained.get("restraint"),
        "autonomous_execution_blocked": True,
        "checked_at": time(),
    }


def get_operational_partner_overview(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.human_centered.operational_companion_runtime import get_operational_companion_overview

    base = get_operational_companion_overview(session_id=session_id)
    brief = render_operational_partner_brief(session_id=session_id)
    return {
        **base,
        "phase": "10.1.4",
        "operational_partner": brief,
        "companion_intelligence": brief.get("companion_quality"),
    }
