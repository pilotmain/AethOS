# SPDX-License-Identifier: Apache-2.0
"""Presence signal pipeline — dedupe, cluster, reason, prioritize."""

from __future__ import annotations

from typing import Any

from aethos_core.presence.attention_authority import attention_quality_summary, rank_with_attention_authority
from aethos_core.presence.presence_clustering import cluster_operational_signals, list_operational_incidents
from aethos_core.presence.presence_reasoning import infer_operational_intent, route_signals_by_context
from aethos_core.presence.presence_recommendation_intelligence import synthesize_intelligent_recommendations
from aethos_core.presence.fatigue.fatigue_authority import apply_fatigue_prevention
from aethos_core.presence.signal_deduplication import deduplicate_signals


def process_presence_signals(
    events: list[dict[str, Any]],
    *,
    user_text: str | None = None,
    focus: dict[str, Any] | None = None,
    window_hours: int = 2,
) -> dict[str, Any]:
    """Full quality pipeline for presence intelligence."""
    intent = infer_operational_intent(user_text, focus=focus)
    deduped = deduplicate_signals(events)
    clusters = cluster_operational_signals(deduped)
    routed = route_signals_by_context(deduped, intent=intent, focus=focus)
    scored = rank_with_attention_authority(routed, focus=focus, clusters=clusters)
    recommendations = synthesize_intelligent_recommendations(clusters=clusters, scored_events=scored)
    quality = attention_quality_summary(scored)
    incidents = list_operational_incidents(clusters)
    fatigue = apply_fatigue_prevention(scored, focus=focus)

    reliability_context = None
    try:
        from aethos_core.reliability.reliability_runtime import assess_operational_reliability

        reliability_context = assess_operational_reliability(
            presence_events=fatigue.get("events") or scored,
            attention_quality=quality,
            recommendations=recommendations,
            focus=focus,
        )
    except Exception:
        pass

    return {
        "intent": intent,
        "events": fatigue.get("events") or scored,
        "clusters": clusters,
        "incidents": incidents,
        "recommendations": recommendations,
        "attention_quality": quality,
        "fatigue": fatigue,
        "reliability": (reliability_context or {}).get("reliability"),
        "reliability_scores": (reliability_context or {}).get("scores"),
        "window_hours": window_hours,
        "autonomous_execution_blocked": True,
    }
