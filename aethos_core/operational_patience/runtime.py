# SPDX-License-Identifier: Apache-2.0
"""Operational patience aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_patience.confidence_patience import assess_confidence_patience
from aethos_core.operational_patience.decay_patience import assess_decay_patience
from aethos_core.operational_patience.execution_patience import assess_execution_patience_intel
from aethos_core.operational_patience.recovery_observation import observe_recovery
from aethos_core.operational_patience.reconciliation_patience import assess_reconciliation_patience
from aethos_core.operational_patience.stabilization_patience import assess_stabilization_patience


def assess_operational_patience(*, provider: str = "railway") -> dict[str, Any]:
    stabilization = {"stabilization_complete": False, "extended_monitoring_active": True}
    execution = assess_execution_patience_intel(stabilization=stabilization, verification={"verified": False})
    stabilization_patience = assess_stabilization_patience(stabilization=stabilization)
    confidence = assess_confidence_patience()
    observation = observe_recovery()
    decay = assess_decay_patience()
    reconciliation = assess_reconciliation_patience(topology_aligned=False)
    maintained = execution.get("premature_claim_blocked", True) and not observation.get("observation_complete")
    return {
        "ok": True,
        "execution_patience": execution,
        "stabilization_patience": stabilization_patience,
        "confidence_patience": confidence,
        "recovery_observation": observation,
        "decay_patience": decay,
        "reconciliation_patience": reconciliation,
        "patience_maintained": maintained,
        "summary": (
            "Primary recovery signals are healthy, though sustained runtime stabilization "
            "continues to be monitored across dependent services."
        ),
    }
