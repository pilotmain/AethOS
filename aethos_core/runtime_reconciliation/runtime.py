# SPDX-License-Identifier: Apache-2.0
"""Runtime reconciliation aggregate — Phase 11.4.3."""

from __future__ import annotations

from typing import Any

from aethos_core.reality_harness_v41.harness_runtime import harness_state
from aethos_core.runtime_reconciliation.reconciliation_runtime import orchestrate_reconciliation


def assess_runtime_reconciliation(*, provider: str = "railway") -> dict[str, Any]:
    """Phase 11.4.3 — runtime reconciliation, operational patience & sustained execution truth."""
    from aethos_core.operational_patience.runtime import assess_operational_patience
    from aethos_core.provider_runtime_truth.runtime import assess_provider_runtime_truth
    from aethos_core.recovery_truth_convergence.runtime import assess_recovery_truth_convergence
    from aethos_core.runtime_decay.runtime import assess_runtime_decay
    from aethos_core.sustained_verification_windows.runtime import assess_sustained_verification_windows

    reconciliation = orchestrate_reconciliation(provider=provider)
    patience = assess_operational_patience(provider=provider)
    decay = assess_runtime_decay()
    provider_truth = assess_provider_runtime_truth()
    windows = assess_sustained_verification_windows()
    recovery = assess_recovery_truth_convergence(provider=provider)
    harness = harness_state()
    converged = (
        reconciliation.get("reconciled")
        and patience.get("patience_maintained")
        and decay.get("decay_bounded")
        and windows.get("window_qualified")
    )
    return {
        "ok": True,
        "phase": "11.4.3",
        "converged": converged,
        "reconciliation": reconciliation,
        "operational_patience": patience,
        "runtime_decay": decay,
        "provider_runtime_truth": provider_truth,
        "verification_windows": windows,
        "recovery_truth": recovery,
        "harness": harness,
        "strategic_position": {
            "conversational_trust": "strong",
            "operational_intelligence": "strong",
            "infrastructure_intelligence": "strong",
            "governance_architecture": "exceptional",
            "runtime_reconciliation": "emerging strong" if not converged else "converging",
            "sustained_verification": "emerging strong",
            "rollback_realism": "emerging",
            "long_tail_operational_trust": "emerging",
            "runtime_convergence_cognition": "next frontier" if not converged else "converging",
        },
        "principles": {
            "operational_truth": "Operational truth is not an event — it is a continuously evolving relationship over time.",
            "runtime_patience": "Mature operational systems wait for sustained convergence before declaring recovery.",
            "provider_vs_runtime": "Provider APIs describe events. Runtime reconciliation describes reality.",
            "runtime_threshold": "Operational trust is earned when execution reality remains stable across time, dependencies, topology, and sustained verification.",
        },
        "summary": reconciliation.get("summary", "Runtime reconciliation assessing."),
        "narrative": reconciliation.get("narrative", "Sustained verification remains active."),
    }
