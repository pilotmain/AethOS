# SPDX-License-Identifier: Apache-2.0
"""Production confidence orchestrator."""

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
from aethos_core.production_confidence.infrastructure_trust_score import compute_infrastructure_trust_score
from aethos_core.production_confidence.recovery_decay_runtime import assess_recovery_decay
from aethos_core.production_confidence.stabilization_confidence import score_stabilization_confidence
from aethos_core.production_confidence.temporal_confidence import assess_temporal_confidence
from aethos_core.production_confidence.topology_stability import score_topology_stability
from aethos_core.production_confidence.verification_confidence import weight_verification_confidence
from aethos_core.recovery_orchestration.runtime import orchestrate_recovery
from aethos_core.reliability_memory.confidence_history import record_confidence_snapshot
from aethos_core.reliability_memory.runtime import assess_reliability_memory


def _lightweight_predictive(
    *,
    verification: dict[str, Any],
    recovery: dict[str, Any],
    drift: dict[str, Any],
    memory: dict[str, Any],
) -> dict[str, Any]:
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
        "predictive_awareness": low_risk,
        "instability": instability,
        "recovery_risk": recovery_risk,
        "exhaustion": exhaustion,
        "topology_risk": topology_risk,
        "trajectory": trajectory,
        "confidence_forecast": confidence_forecast,
    }


def assess_production_confidence(*, runtime_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    verification = assess_continuous_verification(runtime_snapshot=runtime_snapshot)
    recovery = orchestrate_recovery(runtime_snapshot=runtime_snapshot)
    drift = assess_drift_intelligence(runtime_snapshot=runtime_snapshot)
    memory = assess_reliability_memory(runtime_snapshot=runtime_snapshot)
    predictive = _lightweight_predictive(verification=verification, recovery=recovery, drift=drift, memory=memory)
    temporal = assess_temporal_confidence(verification=verification, history=memory)
    stabilization = score_stabilization_confidence(verification=verification, recovery=recovery)
    topology = score_topology_stability(drift=drift)
    verification_conf = weight_verification_confidence(verification=verification)
    recovery_decay = assess_recovery_decay(predictive=predictive)
    trust = compute_infrastructure_trust_score(
        components={
            "temporal": temporal.get("temporal_confidence", 0.5),
            "stabilization": stabilization.get("stabilization_confidence", 0.5),
            "topology": topology.get("topology_stability_score", 0.5),
            "verification": verification_conf.get("verification_confidence", 0.5),
            "recovery": 1.0 - recovery_decay.get("recovery_decay", 0),
        }
    )
    record_confidence_snapshot(score=float(trust.get("infrastructure_trust_score", 0.5)), phase="11.3")
    narrative = _build_narrative(temporal, drift, predictive)
    return {
        "ok": True,
        "phase": "11.3",
        "temporal": temporal,
        "stabilization": stabilization,
        "topology": topology,
        "verification": verification_conf,
        "recovery_decay": recovery_decay,
        "trust": trust,
        "predictive": predictive,
        "memory": memory,
        "narrative": narrative,
        "summary": narrative,
    }


def _build_narrative(temporal: dict[str, Any], drift: dict[str, Any], predictive: dict[str, Any]) -> str:
    if temporal.get("persists") and drift.get("drift_bounded"):
        replay_note = ""
        if drift.get("replay", {}).get("replay_continuity_degraded"):
            replay_note = ", though replay continuity stability still requires longer-duration validation"
        return f"Operational confidence remains strong after extended verification{replay_note}."
    return (
        "Operational confidence building through continuous verification. "
        f"{predictive.get('trajectory', {}).get('summary', '')}"
    )
