# SPDX-License-Identifier: Apache-2.0
"""Reliability runtime — orchestrate reliability authority pipeline."""

from __future__ import annotations

from time import time
from typing import Any

from aethos_core.correlation.correlation_engine import correlate_operational_signals
from aethos_core.explainability.explainability_runtime import build_explainability_bundle
from aethos_core.governance.adaptive.adaptive_governance import assess_adaptive_governance
from aethos_core.governance.adaptive.governance_memory import clear_governance_memory_for_tests
from aethos_core.presence.fatigue.fatigue_authority import apply_fatigue_prevention
from aethos_core.reliability.recovery_runtime import assess_recovery_options
from aethos_core.reliability.reliability_authority import assess_reliability_authority
from aethos_core.reliability.scoring.reliability_scoring import compute_reliability_scores
from aethos_core.replay_intelligence.incident_reconstruction import reconstruct_incident_timeline


def assess_operational_reliability(
    *,
    observations: dict[str, Any] | None = None,
    anomalies: list[dict[str, Any]] | None = None,
    telemetry: dict[str, Any] | None = None,
    trust: dict[str, Any] | None = None,
    replays: list[dict[str, Any]] | None = None,
    attention_quality: dict[str, Any] | None = None,
    presence_events: list[dict[str, Any]] | None = None,
    recommendations: list[dict[str, Any]] | None = None,
    focus: dict[str, Any] | None = None,
    include_reconstruction: bool = False,
) -> dict[str, Any]:
    """Full reliability pipeline — truth, governance, replay, correlation, explainability."""
    obs = observations
    if obs is None:
        from aethos_core.operations.reality_loop import collect_operational_observations

        obs = collect_operational_observations()

    if anomalies is None:
        from aethos_core.intelligence.anomaly_engine import detect_operational_anomalies

        anomalies = detect_operational_anomalies(observations=obs)

    if replays is None:
        from aethos_core.intelligence.operational_replay import list_operational_replays

        replays = list_operational_replays(limit=10)

    if telemetry is None:
        from aethos_core.intelligence.confidence_authority import assess_telemetry_quality

        telemetry = assess_telemetry_quality(
            event_count=len(obs.get("events") or []),
            stale_sources=len((obs.get("telemetry_freshness") or {}).get("stale_sources") or []),
        )

    events = list(presence_events or obs.get("events") or [])
    reliability = assess_reliability_authority(
        observations=obs,
        anomalies=anomalies,
        telemetry=telemetry,
        trust=trust,
        replays=replays,
        attention_quality=attention_quality,
        events=events,
    )
    governance = assess_adaptive_governance(observations=obs, anomalies=anomalies, reliability=reliability)
    correlation = correlate_operational_signals(events=events, anomalies=anomalies)
    fatigue = apply_fatigue_prevention(events, focus=focus)
    scores = compute_reliability_scores(
        observations=obs,
        reliability=reliability,
        attention_quality=attention_quality,
        governance=governance,
        correlation=correlation,
        fatigue=fatigue,
    )
    recovery = assess_recovery_options(reliability=reliability, telemetry=telemetry)
    reconstruction = reconstruct_incident_timeline(window_hours=int(obs.get("window_hours") or 48)) if include_reconstruction else None
    replay_conf = (reconstruction or {}).get("replay_confidence")
    explainability = build_explainability_bundle(
        reliability=reliability,
        governance=governance,
        recommendations=recommendations,
        correlation=correlation,
        replay_confidence=replay_conf,
    )

    return {
        "ok": True,
        "assessed_at": time(),
        "reliability": reliability,
        "governance": governance,
        "scores": scores,
        "correlation": correlation,
        "fatigue": fatigue,
        "recovery": recovery,
        "reconstruction": reconstruction,
        "explainability": explainability,
        "readonly": True,
        "autonomous_execution_blocked": True,
    }


def get_reliability_state() -> dict[str, Any]:
    """Aggregate reliability state for Mission Control."""
    from aethos_core.intelligence.recommendations import list_recommendations
    from aethos_core.presence.collaboration_state import get_collaboration_focus

    result = assess_operational_reliability(
        recommendations=list_recommendations(limit=10),
        focus=get_collaboration_focus(),
    )
    return result


def clear_reliability_state_for_tests() -> None:
    clear_governance_memory_for_tests()
