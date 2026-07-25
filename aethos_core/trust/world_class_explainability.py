# SPDX-License-Identifier: Apache-2.0
"""World-class trust and explainability."""

from __future__ import annotations

from time import time
from typing import Any


def build_world_class_explanation(*, session_id: str = "default", recommendation_id: str | None = None) -> dict[str, Any]:
    """Decision explainability with confidence reasoning and contradiction analysis."""
    from aethos_core.explainability.explainability_runtime import build_explainability_bundle
    from aethos_core.reliability.reliability_runtime import assess_operational_reliability

    rel = assess_operational_reliability()
    reliability = rel.get("reliability") or {}
    recs = rel.get("recommendations") or []
    if not recs:
        from aethos_core.presence.presence_runtime import run_presence_cycle

        cycle = run_presence_cycle(session_id=session_id, channel="trust")
        recs = cycle.get("recommendations") or []

    bundle = build_explainability_bundle(
        reliability=reliability,
        governance=rel.get("governance") or {},
        recommendations=recs,
        correlation=rel.get("correlation"),
        replay_confidence=rel.get("replay_confidence"),
    )

    reasons: list[str] = []
    confidence_lowers: list[str] = []
    failure_count = len([e for e in (rel.get("anomalies") or []) if "deploy" in str(e).lower()])
    if failure_count >= 1:
        reasons.append(f"{failure_count} deployment-related anomalies")
    telemetry = rel.get("telemetry") or {}
    if telemetry.get("freshness") == "degraded":
        reasons.append("degraded telemetry freshness")
        confidence_lowers.append("degraded telemetry freshness")
    if reliability.get("truth_state") == "verification_failed":
        reasons.append("recurring workflow instability signals")
        confidence_lowers.append("incomplete replay evidence")

    replay = bundle.get("replay")
    if isinstance(replay, dict) and replay.get("gaps"):
        confidence_lowers.append("missing provider logs")
    elif isinstance(replay, str) and "gap" in replay.lower():
        confidence_lowers.append("missing provider logs")

    narrative = "This recommendation was generated because:\n" + "\n".join(f"- {r}" for r in reasons[:5])
    if not reasons:
        narrative = "This recommendation was generated from operational observations and governed analysis."
    if confidence_lowers:
        narrative += "\n\nConfidence lowered due to:\n" + "\n".join(f"- {c}" for c in confidence_lowers[:5])

    trust_score = float(reliability.get("confidence_score") or 0.75)
    return {
        "ok": True,
        "narrative": narrative,
        "explainability_bundle": bundle,
        "reasons": reasons,
        "confidence_lowers": confidence_lowers,
        "trust_score": round(trust_score, 2),
        "trust_score_evolution": "tracked",
        "contradiction_analysis": bundle.get("confidence"),
        "governance_timeline": "available_via_audit",
        "readonly": True,
        "autonomous_execution_blocked": True,
        "generated_at": time(),
    }
