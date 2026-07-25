# SPDX-License-Identifier: Apache-2.0
"""Intuition engine — living operational intuition orchestrator."""

from __future__ import annotations

from time import time
from typing import Any

from aethos_core.intuition.attention_prioritizer import prioritize_attention
from aethos_core.intuition.context_shift_detector import detect_context_shift
from aethos_core.intuition.intervention_timing import assess_intervention_timing
from aethos_core.intuition.investigation_prediction import predict_investigation_steps


def assess_operational_intuition(
    *,
    session_id: str = "default",
    user_text: str | None = None,
) -> dict[str, Any]:
    """Predict likely operator needs with calm, relevant prioritization."""
    from aethos_core.conversation.operational_memory import build_continuity_context
    from aethos_core.human_centered.continuity_memory import load_continuity_memory, seed_default_continuity
    from aethos_core.presence.presence_runtime import run_presence_cycle
    from aethos_core.restraint.restraint_runtime import apply_restraint
    from aethos_core.timeline.operational_timeline import get_operational_narrative

    seed_default_continuity(session_id=session_id)
    record = load_continuity_memory(session_id=session_id)
    continuity = build_continuity_context(session_id=session_id)
    cycle = run_presence_cycle(session_id=session_id, channel="intuition")
    events = cycle.get("recommendations") or cycle.get("attention_items") or []

    attention = prioritize_attention(
        session_id=session_id,
        events=[{"title": str(e.get("title", e.get("summary", ""))), **e} for e in events],
        focus_topics=continuity.get("focus_topics"),
    )
    shift = detect_context_shift(session_id=session_id, user_text=user_text)
    timing = assess_intervention_timing(session_id=session_id)
    prediction = predict_investigation_steps(session_id=session_id, context=record.get("focus"))
    narrative = get_operational_narrative(session_id=session_id)

    guidance_lines: list[str] = []
    focus_label = record.get("current_system_focus") or record.get("focus") or "runtime convergence"
    guidance_lines.append(f"You've spent most of today stabilizing **{focus_label}**.")

    can_wait = attention.get("can_wait") or []
    if can_wait:
        guidance_lines.append(f"**{can_wait[0]}** can wait.")

    guidance_lines.append("")
    guidance_lines.append("The highest-impact unresolved issue is:")
    guidance_lines.append(f"**{attention.get('highest_impact_unresolved')}**")

    if not timing.get("should_interrupt"):
        guidance_lines.append("")
        guidance_lines.append(f"*{timing.get('reason')}*")

    guidance = apply_restraint(text="\n".join(guidance_lines), session_id=session_id)

    return {
        "ok": True,
        "phase": "10.1.3",
        "guidance": guidance.get("text", "\n".join(guidance_lines)),
        "attention": attention,
        "context_shift": shift,
        "intervention_timing": timing,
        "investigation_prediction": prediction,
        "operational_narrative": narrative,
        "restraint": guidance.get("restraint"),
        "autonomous_execution_blocked": True,
        "checked_at": time(),
    }
