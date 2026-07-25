# SPDX-License-Identifier: Apache-2.0
"""Operational co-pilot — active operational thinking assistance."""

from __future__ import annotations

from time import time
from typing import Any


def generate_operational_hypotheses(*, session_id: str = "default", context: str | None = None) -> dict[str, Any]:
    """Possible root causes with confidence transparency."""
    from aethos_core.reliability.reliability_runtime import assess_operational_reliability

    rel = assess_operational_reliability()
    reliability = rel.get("reliability") or {}
    truth = reliability.get("truth_state") or "unknown"
    confidence = float(reliability.get("confidence_score") or 0.63)
    telemetry_fresh = (rel.get("telemetry") or {}).get("freshness") or "degraded"

    hypotheses = []
    ctx = (context or "").lower()
    if "deploy" in ctx or truth == "verification_failed":
        hypotheses.append({
            "hypothesis": "Deployment issue started after provider runtime convergence patch",
            "confidence": round(confidence, 2),
            "evidence": ["deployment failures in feed", "verification state"],
        })
    if telemetry_fresh == "degraded" or "telemetry" in ctx:
        hypotheses.append({
            "hypothesis": "Telemetry freshness degradation masking root cause",
            "confidence": round(max(0.4, confidence - 0.15), 2),
            "evidence": ["degraded telemetry freshness"],
        })
    if not hypotheses:
        hypotheses.append({
            "hypothesis": "Operational drift or recurring workflow instability",
            "confidence": round(confidence, 2),
            "evidence": ["operational observations"],
        })

    explanation = (
        f"There's moderate evidence that the primary issue relates to operational instability. "
        f"Confidence is **{confidence:.2f}** because telemetry freshness is **{telemetry_fresh}**."
    )

    return {
        "ok": True,
        "hypotheses": hypotheses,
        "explanation": explanation,
        "investigation_plan": [
            "Review deployment timeline",
            "Correlate workflow failures",
            "Run governed replay walkthrough",
            "Generate preflight proposal (approval required)",
        ],
        "readonly": True,
        "autonomous_execution_blocked": True,
        "generated_at": time(),
    }


def rank_recommendations(*, session_id: str = "default", limit: int = 5) -> dict[str, Any]:
    from aethos_core.presence.presence_runtime import run_presence_cycle

    cycle = run_presence_cycle(session_id=session_id, channel="copilot")
    recs = cycle.get("recommendations") or []
    ranked = []
    for i, r in enumerate(recs[:limit]):
        ranked.append({
            "rank": i + 1,
            "title": r.get("title") or r.get("summary") or f"Recommendation {i + 1}",
            "priority": r.get("priority") or "medium",
            "confidence": r.get("confidence") or 0.6,
            "requires_approval": True,
        })
    return {
        "ok": True,
        "recommendations": ranked,
        "coaching_note": "I'll teach while assisting — bounded by evidence and governance.",
        "autonomous_execution_blocked": True,
    }


def build_copilot_brief(*, session_id: str = "default", user_text: str | None = None) -> str:
    hyp = generate_operational_hypotheses(session_id=session_id, context=user_text)
    ranked = rank_recommendations(session_id=session_id)
    lines = ["**Operational Co-Pilot**", "", hyp.get("explanation", ""), "", "**Hypotheses:**"]
    for h in hyp.get("hypotheses") or []:
        lines.append(f"- {h.get('hypothesis')} (confidence: {h.get('confidence')})")
    lines.append("")
    lines.append("**Ranked recommendations:**")
    for r in ranked.get("recommendations") or []:
        lines.append(f"- [{r.get('rank')}] {r.get('title')} — approval required")
    lines.append("")
    lines.append("*Think continuously. Act only with governance.*")
    return "\n".join(lines)


def get_copilot_status(*, session_id: str = "default") -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "10.1D",
        "features": {
            "operational_hypothesis_engine": True,
            "investigation_planning": True,
            "replay_walkthroughs": True,
            "deployment_impact_analysis": True,
            "recommendation_ranking": True,
            "confidence_explanations": True,
            "operational_coaching": True,
        },
        "autonomous_execution_blocked": True,
    }
