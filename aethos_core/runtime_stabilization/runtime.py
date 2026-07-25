# SPDX-License-Identifier: Apache-2.0
"""Runtime stabilization aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_stabilization.degradation_prediction import predict_degradation
from aethos_core.runtime_stabilization.dependency_pressure import assess_dependency_pressure
from aethos_core.runtime_stabilization.recovery_patience import assess_recovery_patience
from aethos_core.runtime_stabilization.runtime_patience import assess_runtime_patience
from aethos_core.runtime_stabilization.stabilization_runtime import orchestrate_stabilization
from aethos_core.runtime_stabilization.sustained_health import assess_sustained_health
from aethos_core.runtime_stabilization.topology_decay import analyze_topology_decay


def assess_runtime_stabilization(*, verified: bool = False) -> dict[str, Any]:
    stabilization = orchestrate_stabilization(verified=verified)
    verification = {"verified": verified}
    patience = assess_runtime_patience(stabilization=stabilization, verification=verification)
    pressure = assess_dependency_pressure()
    degradation = predict_degradation()
    topology = analyze_topology_decay()
    sustained = assess_sustained_health()
    recovery_patience = assess_recovery_patience(stabilization=stabilization, verification=verification)
    return {
        "ok": True,
        "stabilization": stabilization,
        "patience": patience,
        "recovery_patience": recovery_patience,
        "dependency_pressure": pressure,
        "degradation_prediction": degradation,
        "topology_decay": topology,
        "sustained_health": sustained,
        "summary": (
            "Operational stability remains strong overall, though replay continuity and worker recovery "
            "continue to be monitored across extended operational windows."
        ),
    }
