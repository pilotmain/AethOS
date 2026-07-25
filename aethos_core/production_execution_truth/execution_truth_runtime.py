# SPDX-License-Identifier: Apache-2.0
"""Execution truth runtime — top-level orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.production_execution_truth.execution_patience import assess_execution_patience
from aethos_core.production_execution_truth.deployment_truth import assess_deployment_truth
from aethos_core.production_execution_truth.mutation_truth_convergence import converge_mutation_truth
from aethos_core.production_execution_truth.operational_decay import assess_operational_decay
from aethos_core.production_execution_truth.recovery_truth import assess_recovery_truth
from aethos_core.production_execution_truth.rollback_truth import assess_rollback_truth
from aethos_core.production_execution_truth.stabilization_windows import assess_stabilization_window


def orchestrate_execution_truth(*, provider: str = "railway") -> dict[str, Any]:
    convergence = converge_mutation_truth(provider=provider)
    verification = convergence.get("verification") or {}
    deployment = assess_deployment_truth(provider=provider)
    rollback = assess_rollback_truth(provider=provider)
    window = assess_stabilization_window(verification=verification)
    recovery = assess_recovery_truth(verification=verification)
    decay = assess_operational_decay(base_confidence=0.82)
    patience = assess_execution_patience(stabilization=window, verification=verification)
    return {
        "convergence": convergence,
        "deployment_truth": deployment,
        "rollback_truth": rollback,
        "stabilization_window": window,
        "recovery_truth": recovery,
        "operational_decay": decay,
        "execution_patience": patience,
    }
