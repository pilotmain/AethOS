# SPDX-License-Identifier: Apache-2.0
"""Runtime fragility intelligence — Phase 11.6.4 aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.reality_harness_v44.harness_runtime import harness_state
from aethos_core.runtime_fragility_intelligence.fragility_runtime import orchestrate_runtime_fragility


def assess_runtime_fragility_intelligence(*, provider: str = "railway") -> dict[str, Any]:
    """Phase 11.6.4 — predictive runtime fragility intelligence."""
    from aethos_core.degradation_acceleration.runtime import assess_degradation_acceleration
    from aethos_core.operational_fatigue_cognition.runtime import assess_operational_fatigue_cognition
    from aethos_core.operational_resilience.runtime import assess_operational_resilience
    from aethos_core.predictive_runtime_stability.runtime import assess_predictive_runtime_stability
    from aethos_core.replay_erosion_intelligence.runtime import assess_replay_erosion_intelligence
    from aethos_core.topology_fragility_forecasting.runtime import assess_topology_fragility_forecasting

    fragility = orchestrate_runtime_fragility(provider=provider)
    acceleration = assess_degradation_acceleration(provider=provider)
    replay = assess_replay_erosion_intelligence()
    topology = assess_topology_fragility_forecasting()
    fatigue = assess_operational_fatigue_cognition()
    predictive = assess_predictive_runtime_stability()
    resilience = assess_operational_resilience(provider=provider)
    harness = harness_state()
    fragility_aware = (
        not fragility.get("fragility_emerging")
        and not acceleration.get("acceleration_detected")
        and predictive.get("stability_projected")
        and not fatigue.get("fatigue_elevated")
    )
    return {
        "ok": True,
        "phase": "11.6.4",
        "converged": fragility_aware,
        "runtime_fragility": fragility,
        "degradation_acceleration": acceleration,
        "replay_erosion": replay,
        "topology_fragility": topology,
        "operational_fatigue": fatigue,
        "predictive_stability": predictive,
        "operational_resilience": resilience,
        "harness": harness,
        "strategic_position": {
            "conversational_trust": "production conversational",
            "runtime_reconciliation": "strong",
            "sustained_verification": "strong",
            "runtime_convergence_cognition": "strong",
            "recovery_continuity_intelligence": "strong",
            "operational_resilience_cognition": "strong",
            "runtime_fragility_intelligence": "emerging strong",
            "predictive_degradation_forecasting": "emerging" if not fragility_aware else "converging",
            "long_tail_operational_cognition": "next frontier",
        },
        "principles": {
            "fragility_intelligence_threshold": (
                "Operational trust is earned when systems can sustain resilience, resist degradation, "
                "forecast instability, detect fragility emergence, preserve replay continuity, and maintain topology durability "
                "through evolving runtime pressure over time."
            ),
            "fragility_over_resilience": "Resilience cognition must evolve into runtime fragility intelligence.",
            "calm_monitoring": "Extended fragility monitoring remains active — without panic escalation.",
        },
        "summary": fragility.get("summary", "Runtime fragility intelligence assessing."),
        "narrative": "Extended fragility monitoring remains active.",
    }
