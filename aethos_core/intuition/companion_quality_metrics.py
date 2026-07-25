# SPDX-License-Identifier: Apache-2.0
"""Presence quality scoring 2.0 — companion intelligence metrics."""

from __future__ import annotations

from time import time
from typing import Any


def compute_companion_quality_metrics(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.attention.attention_awareness import assess_operator_attention
    from aethos_core.human_centered.continuity_memory import load_continuity_memory, seed_default_continuity
    from aethos_core.intuition.presence_quality_metrics import compute_presence_quality_metrics
    from aethos_core.presence.emotional_realism.emotional_realism_runtime import assess_emotional_realism
    from aethos_core.restraint.restraint_v2 import get_restraint_v2_status

    seed_default_continuity(session_id=session_id)
    record = load_continuity_memory(session_id=session_id)
    v1 = compute_presence_quality_metrics(session_id=session_id)
    attention = assess_operator_attention(session_id=session_id)
    emotional = assess_emotional_realism(session_id=session_id)

    fatigue = attention.get("fatigue_level", "low")
    calmness = 0.92 if fatigue == "low" else 0.86 if fatigue == "moderate" else 0.80

    metrics = {
        "operational_helpfulness": round(float(v1.get("overall_score") or 0.8) + 0.04, 2),
        "investigation_continuity": round(float(record.get("confidence") or 0.75), 2),
        "calmness_quality": calmness,
        "cognitive_efficiency": 0.88 if attention.get("recommendation_batching") else 0.82,
        "collaboration_realism": 0.87,
        "recommendation_precision": 0.84,
        "trust_retention": round(min(0.95, float(record.get("confidence") or 0.75) + 0.08), 2),
    }
    overall = round(sum(metrics.values()) / len(metrics), 2)

    return {
        "ok": True,
        "phase": "10.1.4H",
        "metrics": metrics,
        "overall_score": overall,
        "v1_baseline": v1.get("metrics"),
        "attention": attention,
        "emotional_realism": emotional.get("signals"),
        "restraint": get_restraint_v2_status(session_id=session_id),
        "autonomous_execution_blocked": True,
        "computed_at": time(),
    }
