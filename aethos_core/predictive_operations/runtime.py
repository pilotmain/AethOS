# SPDX-License-Identifier: Apache-2.0
"""Predictive operations orchestrator."""

from __future__ import annotations

from typing import Any

from aethos_core.continuous_verification.runtime import assess_continuous_verification
from aethos_core.drift_intelligence.runtime import assess_drift_intelligence
from aethos_core.predictive_operations.confidence_forecasting import forecast_confidence_decay
from aethos_core.predictive_operations.instability_prediction import predict_instability
from aethos_core.predictive_operations.operational_trajectory import assess_operational_trajectory
from aethos_core.predictive_operations.recovery_risk_forecast import forecast_recovery_risk
from aethos_core.predictive_operations.resource_exhaustion_prediction import predict_resource_exhaustion
from aethos_core.predictive_operations.topology_risk_projection import project_topology_risk
from aethos_core.recovery_orchestration.runtime import orchestrate_recovery
from aethos_core.reliability_memory.runtime import assess_reliability_memory


def assess_predictive_operations(*, runtime_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    verification = assess_continuous_verification(runtime_snapshot=runtime_snapshot)
    drift = assess_drift_intelligence(runtime_snapshot=runtime_snapshot)
    recovery = orchestrate_recovery(runtime_snapshot=runtime_snapshot)
    memory = assess_reliability_memory(runtime_snapshot=runtime_snapshot)
    infrastructure = verification.get("infrastructure") or {}
    instability = predict_instability(drift=drift)
    recovery_risk = forecast_recovery_risk(recovery=recovery)
    exhaustion = predict_resource_exhaustion(infrastructure=infrastructure)
    topology_risk = project_topology_risk(drift=drift)
    trajectory = assess_operational_trajectory(memory=memory)
    confidence_forecast = forecast_confidence_decay(verification=verification, drift=drift)
    low_risk = (
        instability.get("instability_risk", 1) < 0.4
        and recovery_risk.get("recovery_failure_probability", 1) < 0.4
        and confidence_forecast.get("confidence_persists")
    )
    return {
        "ok": True,
        "predictive_awareness": low_risk,
        "maturity": "stable" if low_risk else "beta",
        "instability": instability,
        "recovery_risk": recovery_risk,
        "exhaustion": exhaustion,
        "topology_risk": topology_risk,
        "trajectory": trajectory,
        "confidence_forecast": confidence_forecast,
        "principle": "Operational intelligence becomes truly valuable when it identifies instability before failures fully emerge.",
        "summary": trajectory.get("summary", ""),
    }
