# SPDX-License-Identifier: Apache-2.0
"""Operational companion runtime — Phase 10.1.3 calm intelligence orchestrator."""

from __future__ import annotations

from time import time
from typing import Any


def render_operational_companion_brief(*, session_id: str = "default", user_text: str | None = None) -> dict[str, Any]:
    """Slice J end-state — calm, aware, collaborative companion brief."""
    from aethos_core.collaboration.human_quality.collaboration_quality import shape_collaborative_phrasing
    from aethos_core.conversation.flow.conversation_flow import apply_conversation_flow
    from aethos_core.human_centered.continuity_memory import load_continuity_memory, seed_default_continuity
    from aethos_core.intuition.intuition_engine import assess_operational_intuition
    from aethos_core.intuition.investigation_prediction import predict_investigation_steps
    from aethos_core.intuition.presence_quality_metrics import compute_presence_quality_metrics
    from aethos_core.restraint.restraint_runtime import apply_restraint
    from aethos_core.timeline.operational_timeline import _load_conversation_threads, get_operational_narrative
    from aethos_core.trust.living_explainability import build_living_explanation

    seed_default_continuity(session_id=session_id)
    record = load_continuity_memory(session_id=session_id)
    intuition = assess_operational_intuition(session_id=session_id, user_text=user_text)
    narrative = get_operational_narrative(session_id=session_id)
    prediction = predict_investigation_steps(session_id=session_id)
    metrics = compute_presence_quality_metrics(session_id=session_id)

    remaining = (record.get("pending_validation") or record.get("unresolved") or ["replay integrity during long-running sessions"])[0]
    collab = shape_collaborative_phrasing(
        resolved=record.get("resolved"),
        remaining=remaining,
        confidence=float(record.get("confidence") or 0.72),
    )

    core_parts = [
        narrative.get("story", ""),
        intuition.get("guidance", ""),
        build_living_explanation(session_id=session_id),
        collab,
        "I can:",
    ]
    for step in (prediction.get("predicted_steps") or [])[:4]:
        core_parts.append(f"- {step}")

    core = "\n".join(p for p in core_parts if p and str(p).strip())
    restrained = apply_restraint(text=core, session_id=session_id)
    has_threads = bool(_load_conversation_threads(session_id=session_id))
    flowed = apply_conversation_flow(
        session_id=session_id,
        core_text=restrained.get("text", core),
        confidence=float(record.get("confidence") or 0.72),
        verbosity="high" if has_threads else "medium",
    )

    return {
        "ok": True,
        "phase": "10.1.3",
        "identity": "operational companion",
        "principle": "present, helpful, calm, aware, and trustworthy",
        "brief": flowed,
        "brief_core": core,
        "intuition": intuition,
        "narrative": narrative,
        "presence_quality": metrics,
        "intervention_timing": intuition.get("intervention_timing"),
        "autonomous_execution_blocked": True,
        "checked_at": time(),
    }


def get_operational_companion_overview(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.human_centered.living_companion_runtime import get_living_companion_overview

    base = get_living_companion_overview(session_id=session_id)
    brief = render_operational_companion_brief(session_id=session_id)
    return {
        **base,
        "phase": "10.1.3",
        "operational_companion": brief,
        "calm_intelligence": brief.get("presence_quality"),
    }
