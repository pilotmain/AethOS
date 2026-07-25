# SPDX-License-Identifier: Apache-2.0
"""Production execution truth — Phase 11.6 aggregate runtime."""

from __future__ import annotations

from typing import Any

from aethos_core.infrastructure_truth.runtime import assess_infrastructure_truth
from aethos_core.production_execution_truth.execution_truth_runtime import orchestrate_execution_truth
from aethos_core.production_execution_truth.production_qualification import assess_production_qualification
from aethos_core.provider_truth_convergence.runtime import assess_provider_truth_convergence
from aethos_core.reality_harness_v4.harness_runtime import harness_state
from aethos_core.rollback_integrity.runtime import assess_rollback_integrity
from aethos_core.runtime_stabilization.runtime import assess_runtime_stabilization
from aethos_core.sustained_verification.runtime import assess_sustained_verification


def assess_production_execution_truth(*, provider: str = "railway") -> dict[str, Any]:
    """Phase 11.6 — production execution realism, runtime truth & sustained operational verification."""
    execution = orchestrate_execution_truth(provider=provider)
    providers = assess_provider_truth_convergence()
    rollback = assess_rollback_integrity(provider=provider)
    verified = execution["convergence"].get("verification", {}).get("verified", False)
    stabilization = assess_runtime_stabilization(verified=verified)
    infrastructure = assess_infrastructure_truth()
    sustained = assess_sustained_verification()
    harness = harness_state()
    qualification = assess_production_qualification(
        deployment=execution["deployment_truth"],
        rollback=rollback,
        stabilization=stabilization,
        infrastructure=infrastructure,
        harness=harness,
        decay=execution["operational_decay"],
        sustained=sustained,
    )
    converged = qualification.get("production_reliable", False) and sustained.get("sustained_qualified", False)
    return {
        "ok": True,
        "phase": "11.6",
        "converged": converged,
        "qualification_tier": qualification.get("qualification_tier"),
        "execution_truth": execution,
        "provider_truth": providers,
        "rollback_integrity": rollback,
        "runtime_stabilization": stabilization,
        "infrastructure_truth": infrastructure,
        "sustained_verification": sustained,
        "harness": harness,
        "production_qualification": qualification,
        "strategic_position": {
            "conversational_reliability": "strong",
            "human_interaction_quality": "strong",
            "infrastructure_intelligence": "strong",
            "governance_architecture": "exceptional",
            "operational_cognition": "strong",
            "runtime_reconciliation": "emerging" if not converged else "converging",
            "rollback_realism": "emerging",
            "sustained_verification": "emerging" if not sustained.get("sustained_qualified") else "converging",
            "production_execution_truth": "next frontier" if not converged else "converging",
        },
        "principles": {
            "execution_truth": "An operational system becomes trustworthy when reality stabilizes, dependencies recover, drift remains bounded, and operational health persists over time.",
            "provider_signals": "Provider APIs are signals — not operational truth by themselves.",
            "infrastructure_truth": "Infrastructure truth is sustained operational convergence — not temporary health snapshots.",
            "operational_threshold": "Operational systems become trustworthy when execution reality, runtime stabilization, rollback integrity, topology recovery, and sustained verification all converge over time.",
        },
        "summary": execution["convergence"].get("summary", "Production execution truth assessing."),
        "narrative": execution["convergence"].get("narrative", "Extended monitoring remains active."),
    }
