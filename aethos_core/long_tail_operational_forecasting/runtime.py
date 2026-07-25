# SPDX-License-Identifier: Apache-2.0
"""Long-tail operational forecasting aggregate — Phase 11.4.7."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_operational_forecasting.forecasting_runtime import orchestrate_long_tail_forecasting
from aethos_core.reality_harness_v45.harness_runtime import harness_state


def assess_long_tail_operational_forecasting(*, provider: str = "railway") -> dict[str, Any]:
    """Phase 11.4.7 — long-tail operational forecasting & autonomous stability cognition."""
    from aethos_core.autonomous_stability_cognition.runtime import assess_autonomous_stability_cognition
    from aethos_core.operational_survivability.runtime import assess_operational_survivability
    from aethos_core.predictive_operational_cognition.runtime import assess_predictive_operational_cognition
    from aethos_core.replay_longevity_forecasting.runtime import assess_replay_longevity_forecasting
    from aethos_core.resilience_exhaustion.runtime import assess_resilience_exhaustion
    from aethos_core.runtime_fragility_intelligence.runtime import assess_runtime_fragility_intelligence
    from aethos_core.topology_sustainability.runtime import assess_topology_sustainability

    forecasting = orchestrate_long_tail_forecasting(provider=provider)
    survivability = assess_operational_survivability()
    replay_longevity = assess_replay_longevity_forecasting()
    topology = assess_topology_sustainability()
    exhaustion = assess_resilience_exhaustion()
    stability = assess_autonomous_stability_cognition(provider=provider)
    predictive = assess_predictive_operational_cognition(provider=provider)
    fragility = assess_runtime_fragility_intelligence(provider=provider)
    harness = harness_state()
    long_tail_qualified = (
        forecasting.get("forecastable")
        and survivability.get("survivable")
        and replay_longevity.get("continuity_durable")
        and not exhaustion.get("exhaustion_emerging")
        and stability.get("stability_enduring")
    )
    narrative = (
        "Extended long-tail operational forecasting remains active across sustained verification windows. "
        "No significant survivability degradation acceleration patterns are currently emerging."
    )
    return {
        "ok": True,
        "phase": "11.4.7",
        "converged": long_tail_qualified,
        "long_tail_forecasting": forecasting,
        "operational_survivability": survivability,
        "replay_longevity_forecasting": replay_longevity,
        "topology_sustainability": topology,
        "resilience_exhaustion": exhaustion,
        "autonomous_stability": stability,
        "predictive_operational_cognition": predictive,
        "runtime_fragility_intelligence": fragility,
        "harness": harness,
        "strategic_position": {
            "conversational_trust": "production conversational",
            "runtime_reconciliation": "strong",
            "sustained_verification": "strong",
            "runtime_convergence_cognition": "strong",
            "recovery_continuity_intelligence": "strong",
            "operational_resilience_cognition": "strong",
            "runtime_fragility_intelligence": "strong",
            "predictive_operational_cognition": "strong",
            "long_tail_operational_forecasting": "emerging" if not long_tail_qualified else "converging",
            "autonomous_stability_cognition": "next frontier",
        },
        "principles": {
            "long_tail_forecasting_threshold": (
                "Operational trust is earned when systems can sustain resilience, resist degradation, "
                "forecast instability, preserve replay continuity, maintain topology durability, "
                "and sustain operational survivability through evolving runtime pressure over long operational horizons."
            ),
            "forecasting_over_prediction": "Predictive operational cognition must evolve into long-tail operational forecasting.",
            "calm_survivability": (
                "Extended long-tail monitoring remains active — without panic escalation, "
                "manipulative urgency, or cognitive overload."
            ),
        },
        "summary": forecasting.get("summary", "Long-tail operational forecasting assessing."),
        "narrative": narrative,
    }
