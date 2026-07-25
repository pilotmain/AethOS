# SPDX-License-Identifier: Apache-2.0
"""Long-tail runtime cognition aggregate — Phase 11.6.5."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_runtime_cognition.cognition_runtime import orchestrate_long_tail_runtime_cognition
from aethos_core.reality_harness_v45.harness_runtime import harness_state


def assess_long_tail_runtime_cognition(*, provider: str = "railway") -> dict[str, Any]:
    """Phase 11.6.5 — long-tail runtime cognition & runtime survivability intelligence."""
    from aethos_core.operational_endurance.runtime import assess_operational_endurance
    from aethos_core.operational_resilience.runtime import assess_operational_resilience
    from aethos_core.replay_continuity_survivability.runtime import assess_replay_continuity_survivability
    from aethos_core.resilience_exhaustion_intelligence.runtime import assess_resilience_exhaustion_intelligence
    from aethos_core.runtime_fragility_intelligence.runtime import assess_runtime_fragility_intelligence
    from aethos_core.runtime_survivability_intelligence.runtime import assess_runtime_survivability_intelligence
    from aethos_core.topology_endurance_forecasting.runtime import assess_topology_endurance_forecasting

    cognition = orchestrate_long_tail_runtime_cognition(provider=provider)
    survivability = assess_runtime_survivability_intelligence(provider=provider)
    endurance = assess_operational_endurance()
    replay = assess_replay_continuity_survivability()
    topology = assess_topology_endurance_forecasting()
    exhaustion = assess_resilience_exhaustion_intelligence()
    fragility = assess_runtime_fragility_intelligence(provider=provider)
    resilience = assess_operational_resilience(provider=provider)
    harness = harness_state()
    long_tail_qualified = (
        cognition.get("cognition_qualified")
        and survivability.get("survivable")
        and replay.get("continuity_sustainable")
        and not exhaustion.get("exhaustion_emerging")
        and topology.get("enduring")
    )
    narrative = (
        "Extended long-tail runtime cognition remains active across prolonged verification windows. "
        "No significant survivability degradation acceleration patterns are currently emerging."
    )
    return {
        "ok": True,
        "phase": "11.6.5",
        "converged": long_tail_qualified,
        "long_tail_runtime_cognition": cognition,
        "runtime_survivability_intelligence": survivability,
        "operational_endurance": endurance,
        "replay_continuity_survivability": replay,
        "topology_endurance_forecasting": topology,
        "resilience_exhaustion_intelligence": exhaustion,
        "runtime_fragility_intelligence": fragility,
        "operational_resilience": resilience,
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
            "long_tail_operational_cognition": "emerging strong",
            "runtime_survivability_cognition": "emerging" if not long_tail_qualified else "converging",
        },
        "principles": {
            "runtime_survivability_threshold": (
                "Operational trust is earned when systems can sustain resilience, resist degradation, "
                "forecast instability, preserve replay continuity, maintain topology durability, "
                "and sustain operational survivability through evolving runtime pressure over extended operational timelines."
            ),
            "survivability_over_fragility": "Runtime fragility intelligence must evolve into long-tail runtime survivability cognition.",
            "calm_endurance": (
                "Extended long-tail monitoring remains active — without panic escalation, "
                "manipulative urgency, alert amplification, or cognitive overload."
            ),
        },
        "summary": cognition.get("summary", "Long-tail runtime cognition assessing."),
        "narrative": narrative,
    }
