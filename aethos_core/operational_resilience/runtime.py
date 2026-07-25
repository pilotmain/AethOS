# SPDX-License-Identifier: Apache-2.0
"""Operational resilience — Phase 11.6.3 aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_resilience.resilience_runtime import orchestrate_resilience
from aethos_core.reality_harness_v43.harness_runtime import harness_state


def assess_operational_resilience(*, provider: str = "railway") -> dict[str, Any]:
    """Phase 11.6.3 — resilience-aware operational cognition."""
    from aethos_core.kubernetes_runtime_durability.runtime import assess_kubernetes_runtime_durability
    from aethos_core.long_tail_resilience.runtime import assess_long_tail_resilience
    from aethos_core.recovery_continuity.runtime import assess_recovery_continuity_intelligence
    from aethos_core.replay_resilience.runtime import assess_replay_resilience_cognition
    from aethos_core.runtime_fragility.runtime import assess_runtime_fragility
    from aethos_core.sustained_trust_evolution.runtime import assess_sustained_trust_evolution

    resilience = orchestrate_resilience(provider=provider)
    fragility = assess_runtime_fragility(provider=provider)
    trust = assess_sustained_trust_evolution()
    kubernetes = assess_kubernetes_runtime_durability()
    replay = assess_replay_resilience_cognition()
    memory = assess_long_tail_resilience(provider=provider)
    continuity = assess_recovery_continuity_intelligence(provider=provider)
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
        "phase": "11.6.3",
        "converged": resilience_established,
        "operational_resilience": resilience,
        "runtime_fragility": fragility,
        "sustained_trust_evolution": trust,
        "kubernetes_durability": kubernetes,
        "replay_resilience": replay,
        "long_tail_resilience": memory,
        "recovery_continuity": continuity,
        "harness": harness,
        "strategic_position": {
            "conversational_trust": "production conversational",
            "runtime_reconciliation": "strong",
            "sustained_verification": "strong",
            "runtime_convergence_cognition": "strong",
            "recovery_continuity_intelligence": "strong",
            "infrastructure_convergence": "strong",
            "temporal_operational_trust": "emerging strong",
            "operational_resilience_cognition": "emerging" if not resilience_established else "converging",
            "runtime_fragility_intelligence": "next frontier" if not resilience_established else "emerging",
        },
        "principles": {
            "operational_resilience_threshold": (
                "Operational trust is earned when systems remain resilient, stable, and operationally trustworthy "
                "through evolving runtime conditions, topology pressure, dependency stress, replay persistence, "
                "and long-tail degradation — not merely because recovery once appeared successful."
            ),
            "resilience_over_continuity": "Continuity intelligence must evolve into resilience cognition.",
            "adaptive_verification": "Extended operational verification remains active.",
        },
        "summary": resilience.get("summary", "Operational resilience assessing."),
        "narrative": "Extended operational verification remains active.",
    }
