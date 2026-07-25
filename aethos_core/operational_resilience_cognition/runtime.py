# SPDX-License-Identifier: Apache-2.0
"""Operational resilience cognition — Phase 11.4.5 aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_resilience_cognition.resilience_runtime import orchestrate_operational_resilience
from aethos_core.reality_harness_v43.harness_runtime import harness_state


def assess_operational_resilience_cognition(*, provider: str = "railway") -> dict[str, Any]:
    """Phase 11.4.5 — resilience-aware operational cognition."""
    from aethos_core.infrastructure_fragility.runtime import assess_infrastructure_fragility
    from aethos_core.kubernetes_resilience.runtime import assess_kubernetes_resilience
    from aethos_core.long_tail_resilience_memory.runtime import assess_long_tail_resilience_memory
    from aethos_core.replay_resilience_intelligence.runtime import assess_replay_resilience_intelligence
    from aethos_core.runtime_convergence_cognition.runtime import assess_runtime_convergence_cognition
    from aethos_core.temporal_trust_evolution.runtime import assess_temporal_trust_evolution

    resilience = orchestrate_operational_resilience(provider=provider)
    fragility = assess_infrastructure_fragility(provider=provider)
    trust = assess_temporal_trust_evolution()
    kubernetes = assess_kubernetes_resilience()
    replay = assess_replay_resilience_intelligence()
    memory = assess_long_tail_resilience_memory(provider=provider)
    convergence = assess_runtime_convergence_cognition(provider=provider)
    harness = harness_state()
    resilience_established = (
        resilience.get("resilient")
        and not fragility.get("fragility_elevated")
        and trust.get("trust_evolving")
        and replay.get("resilient")
        and memory.get("memory_active")
    )
    return {
        "ok": True,
        "phase": "11.4.5",
        "converged": resilience_established,
        "operational_resilience": resilience,
        "infrastructure_fragility": fragility,
        "temporal_trust_evolution": trust,
        "kubernetes_resilience": kubernetes,
        "replay_resilience": replay,
        "resilience_memory": memory,
        "runtime_convergence": convergence,
        "harness": harness,
        "strategic_position": {
            "conversational_trust": "production conversational",
            "runtime_reconciliation": "strong",
            "sustained_verification": "strong",
            "runtime_convergence_cognition": "strong",
            "infrastructure_intuition": "strong",
            "temporal_trust_evolution": "emerging strong",
            "recovery_continuity_intelligence": "emerging strong",
            "operational_resilience_cognition": "emerging" if not resilience_established else "converging",
            "infrastructure_fragility_intelligence": "next frontier" if not resilience_established else "emerging",
        },
        "principles": {
            "resilience_cognition_threshold": (
                "Operational trust is earned when systems remain resilient, stable, and operationally trustworthy "
                "through evolving runtime conditions, topology pressure, dependency stress, and long-tail degradation — "
                "not merely because they recovered once."
            ),
            "resilience_over_convergence": "Operational convergence must evolve into operational resilience cognition.",
            "adaptive_verification": "Extended reconciliation remains active.",
        },
        "summary": resilience.get("summary", "Operational resilience cognition assessing."),
        "narrative": "Extended reconciliation remains active.",
    }
