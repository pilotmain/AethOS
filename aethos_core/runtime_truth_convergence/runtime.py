# SPDX-License-Identifier: Apache-2.0
"""Runtime truth convergence — Phase 11.6.1 aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.reality_harness_v41.harness_runtime import harness_state
from aethos_core.runtime_truth_convergence.runtime_truth_runtime import orchestrate_runtime_truth


def assess_runtime_truth_convergence(*, provider: str = "railway") -> dict[str, Any]:
    """Phase 11.6.1 — runtime truth convergence & production reliability maturity."""
    from aethos_core.adaptive_sustained_verification.runtime import assess_adaptive_sustained_verification
    from aethos_core.long_tail_operational_decay.runtime import assess_long_tail_operational_decay
    from aethos_core.operational_stability_windows.runtime import assess_operational_stability_windows
    from aethos_core.provider_runtime_truth.provider_truth_memory import record_provider_convergence
    from aethos_core.provider_runtime_truth.railway_sustained_truth import assess_railway_sustained_truth
    from aethos_core.recovery_convergence.runtime import assess_recovery_convergence

    runtime_truth = orchestrate_runtime_truth(provider=provider)
    stability_windows = assess_operational_stability_windows()
    recovery = assess_recovery_convergence(provider=provider)
    long_tail_decay = assess_long_tail_operational_decay()
    adaptive = assess_adaptive_sustained_verification()
    provider_sustained = assess_railway_sustained_truth()
    provider_memory = record_provider_convergence(provider=provider, converged=provider_sustained.get("sustained_converged", False))
    harness = harness_state()
    converged = (
        runtime_truth.get("converged")
        and stability_windows.get("window_qualified")
        and long_tail_decay.get("decay_bounded")
        and adaptive.get("adaptively_qualified")
    )
    return {
        "ok": True,
        "phase": "11.6.1",
        "converged": converged,
        "runtime_truth": runtime_truth,
        "stability_windows": stability_windows,
        "recovery_convergence": recovery,
        "long_tail_decay": long_tail_decay,
        "adaptive_verification": adaptive,
        "provider_sustained_truth": provider_sustained,
        "provider_memory": provider_memory,
        "harness": harness,
        "strategic_position": {
            "conversational_trust": "production conversational",
            "operational_intelligence": "strong",
            "infrastructure_intelligence": "strong",
            "provider_execution_realism": "strong",
            "runtime_reconciliation": "strong",
            "sustained_verification": "strong",
            "long_tail_operational_trust": "emerging strong" if not converged else "converging",
            "topology_convergence_cognition": "emerging",
            "recovery_continuity_intelligence": "next frontier",
        },
        "principles": {
            "sustained_trust": "Operational trust is earned when stability continues to converge through topology, replay, dependencies, and sustained runtime health over time.",
            "provider_vs_truth": "Provider success signals represent events. Operational truth represents sustained convergence.",
            "recovery_complete": "Recovery is complete when systems remain stable — not when they return.",
            "progressive_decay": "Operational degradation is usually progressive — not immediate.",
        },
        "summary": runtime_truth.get("summary", "Runtime truth convergence assessing."),
        "narrative": runtime_truth.get("narrative", "Extended reconciliation remains active."),
    }
