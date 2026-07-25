# SPDX-License-Identifier: Apache-2.0
"""Operational truth API — capability hardening and production proof."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["operational-truth"])


class HarnessCycleRequest(BaseModel):
    window_hours: int = 48
    source: str = "api"


@router.get("/operational-truth/state")
def operational_truth_state_api() -> dict[str, Any]:
    from aethos_core.operational_truth.runtime import get_operational_truth_state

    return get_operational_truth_state()


@router.get("/operational-truth/full")
def operational_truth_full_api() -> dict[str, Any]:
    from aethos_core.operational_truth.runtime import assess_operational_truth

    return assess_operational_truth()


@router.get("/operational-truth/capability-matrix")
def capability_matrix_api() -> dict[str, Any]:
    from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix, matrix_summary

    matrix = build_capability_truth_matrix()
    return {"ok": True, "matrix": matrix, "summary": matrix_summary(matrix)}


@router.get("/operational-truth/providers")
def provider_readiness_api() -> dict[str, Any]:
    from aethos_core.operational_truth.capability_registry import provider_hardening_priority
    from aethos_core.operational_truth.operational_readiness import assess_operational_readiness

    return {
        "ok": True,
        "providers": provider_hardening_priority(),
        "readiness": assess_operational_readiness(),
    }


@router.get("/operational-truth/audit")
def capability_audit_api() -> dict[str, Any]:
    from aethos_core.operational_truth.capability_audit import run_capability_audit

    return {"ok": True, **run_capability_audit()}


@router.get("/operational-truth/confidence-integrity")
def confidence_integrity_api() -> dict[str, Any]:
    from aethos_core.confidence_integrity.integrity_runtime import assess_confidence_integrity
    from aethos_core.reliability.reliability_runtime import assess_operational_reliability

    rel = assess_operational_reliability()
    confidence_detail = (rel.get("reliability") or {}).get("confidence_detail") or {}
    telemetry = rel.get("telemetry") or {}
    replay = rel.get("replay") or {}
    verified = bool((rel.get("reliability") or {}).get("verified"))

    return assess_confidence_integrity(
        raw_confidence=float(confidence_detail.get("raw_confidence") or 0.72),
        telemetry_quality=str(telemetry.get("telemetry_quality") or "medium"),
        stale_sources=len((telemetry.get("stale_sources") or [])) if isinstance(telemetry.get("stale_sources"), list) else int(telemetry.get("stale_count") or 0),
        replay_gaps=int(replay.get("gap_count") or 0),
        verified=verified,
    )


@router.get("/reality-harness/state")
def reality_harness_state_api() -> dict[str, Any]:
    from aethos_core.reality_harness.harness_runtime import harness_state

    return harness_state()


@router.post("/reality-harness/cycle")
def reality_harness_cycle_api(body: HarnessCycleRequest | None = None) -> dict[str, Any]:
    from aethos_core.reality_harness.harness_runtime import run_reality_harness_cycle

    req = body or HarnessCycleRequest()
    return run_reality_harness_cycle(window_hours=req.window_hours, source=req.source)


@router.get("/reality-harness/scenarios")
def reality_harness_scenarios_api() -> dict[str, Any]:
    from aethos_core.reality_harness.scenarios import list_reality_scenarios

    return {"ok": True, "scenarios": list_reality_scenarios()}


@router.get("/mutation-reliability/{job_id}")
def mutation_reliability_api(job_id: str) -> dict[str, Any]:
    from aethos_core.mutation_reliability.reliability_runtime import assess_mutation_reliability

    result = assess_mutation_reliability(mutation_job_id=job_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/verification/jobs/{job_id}")
def verification_job_api(job_id: str) -> dict[str, Any]:
    from aethos_core.verification.execution_verifier import verify_execution_outcome

    result = verify_execution_outcome(mutation_job_id=job_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/production-reliability/providers")
def production_reliability_providers_api() -> dict[str, Any]:
    from aethos_core.provider_hardening.verify import tier1_provider_reliability

    return {"ok": True, "providers": tier1_provider_reliability(), "harness_version": "2.0"}


@router.get("/production-reliability/reconciliation/{job_id}")
def mutation_reconciliation_api(job_id: str) -> dict[str, Any]:
    from aethos_core.reconciliation.mutation_reconciliation import reconcile_mutation

    result = reconcile_mutation(mutation_job_id=job_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/production-reliability/recovery/{job_id}")
def recovery_runtime_api(job_id: str) -> dict[str, Any]:
    from aethos_core.recovery_runtime.runtime import assess_recovery_state

    result = assess_recovery_state(mutation_job_id=job_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/production-reliability/state")
def production_reliability_state_api() -> dict[str, Any]:
    from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix, matrix_summary
    from aethos_core.provider_hardening.verify import tier1_provider_reliability
    from aethos_core.reality_harness.harness_runtime import harness_state

    matrix = build_capability_truth_matrix()
    tier1 = [r for r in matrix if r.get("provider") in ("railway", "github", "vercel")]
    return {
        "ok": True,
        "harness_version": "2.0",
        "tier1_providers": tier1_provider_reliability(),
        "tier1_capabilities": tier1,
        "matrix_summary": matrix_summary(matrix),
        "harness": harness_state(),
    }


@router.get("/infrastructure-intelligence/state")
def infrastructure_intelligence_state_api() -> dict[str, Any]:
    from aethos_core.infrastructure_intelligence.runtime import assess_infrastructure_state

    return assess_infrastructure_state()


@router.get("/infrastructure-intelligence/docker")
def infrastructure_docker_api() -> dict[str, Any]:
    from aethos_core.infrastructure.docker.runtime import analyze_docker_runtime

    return analyze_docker_runtime()


@router.get("/infrastructure-intelligence/kubernetes")
def infrastructure_kubernetes_api() -> dict[str, Any]:
    from aethos_core.infrastructure.kubernetes.runtime import verify_kubernetes_rollout

    return verify_kubernetes_rollout()


@router.get("/infrastructure-intelligence/topology")
def infrastructure_topology_api() -> dict[str, Any]:
    from aethos_core.topology.runtime import build_topology_intelligence

    return build_topology_intelligence()


@router.get("/infrastructure-intelligence/reconciliation")
def infrastructure_reconciliation_api() -> dict[str, Any]:
    from aethos_core.infrastructure_reconciliation.runtime import reconcile_infrastructure

    return reconcile_infrastructure()


@router.get("/infrastructure-intelligence/confidence")
def infrastructure_confidence_api() -> dict[str, Any]:
    from aethos_core.infrastructure_confidence.runtime import assess_infrastructure_confidence

    return assess_infrastructure_confidence()


@router.get("/infrastructure-intelligence/harness/scenarios")
def infrastructure_harness_scenarios_api() -> dict[str, Any]:
    from aethos_core.infrastructure_harness.harness_runtime import harness_state

    return harness_state()


@router.get("/operational-reliability/state")
def operational_reliability_state_api() -> dict[str, Any]:
    from aethos_core.operational_reliability.runtime import assess_operational_reliability

    return assess_operational_reliability()


@router.get("/operational-reliability/continuous-verification")
def continuous_verification_api() -> dict[str, Any]:
    from aethos_core.continuous_verification.runtime import assess_continuous_verification

    return assess_continuous_verification()


@router.get("/operational-reliability/recovery-orchestration")
def recovery_orchestration_api() -> dict[str, Any]:
    from aethos_core.recovery_orchestration.runtime import orchestrate_recovery

    return orchestrate_recovery()


@router.get("/operational-reliability/drift-intelligence")
def drift_intelligence_api() -> dict[str, Any]:
    from aethos_core.drift_intelligence.runtime import assess_drift_intelligence

    return assess_drift_intelligence()


@router.get("/operational-reliability/predictive-operations")
def predictive_operations_api() -> dict[str, Any]:
    from aethos_core.predictive_operations.runtime import assess_predictive_operations

    return assess_predictive_operations()


@router.get("/operational-reliability/production-confidence")
def production_confidence_api() -> dict[str, Any]:
    from aethos_core.production_confidence.runtime import assess_production_confidence

    return assess_production_confidence()


@router.get("/operational-reliability/reliability-memory")
def reliability_memory_api() -> dict[str, Any]:
    from aethos_core.reliability_memory.runtime import assess_reliability_memory

    return assess_reliability_memory()


@router.get("/operational-reliability/harness/scenarios")
def reliability_harness_scenarios_api() -> dict[str, Any]:
    from aethos_core.reliability_harness.harness_runtime import harness_state

    return harness_state()


@router.get("/production-execution-truth/state")
def production_execution_truth_state_api() -> dict[str, Any]:
    from aethos_core.production_execution_truth.runtime import assess_production_execution_truth

    return assess_production_execution_truth()


@router.get("/production-execution-truth/providers")
def production_execution_truth_providers_api() -> dict[str, Any]:
    from aethos_core.provider_truth_convergence.runtime import assess_provider_truth_convergence

    return assess_provider_truth_convergence()


@router.get("/production-execution-truth/rollback")
def production_execution_truth_rollback_api() -> dict[str, Any]:
    from aethos_core.rollback_integrity.runtime import assess_rollback_integrity

    return assess_rollback_integrity()


@router.get("/production-execution-truth/stabilization")
def production_execution_truth_stabilization_api() -> dict[str, Any]:
    from aethos_core.runtime_stabilization.runtime import assess_runtime_stabilization

    return assess_runtime_stabilization()


@router.get("/production-execution-truth/infrastructure")
def production_execution_truth_infrastructure_api() -> dict[str, Any]:
    from aethos_core.infrastructure_truth.runtime import assess_infrastructure_truth

    return assess_infrastructure_truth()


@router.get("/reality-harness-v4/scenarios")
def reality_harness_v4_scenarios_api() -> dict[str, Any]:
    from aethos_core.reality_harness_v4.harness_runtime import harness_state

    return harness_state()


@router.get("/production-execution-truth/sustained-verification")
def production_execution_sustained_verification_api() -> dict[str, Any]:
    from aethos_core.sustained_verification.runtime import assess_sustained_verification

    return assess_sustained_verification()


@router.get("/production-execution-realism/state")
def production_execution_realism_state_api() -> dict[str, Any]:
    from aethos_core.production_execution.runtime import assess_production_execution_realism

    return assess_production_execution_realism()


@router.get("/runtime-reconciliation/state")
def runtime_reconciliation_state_api() -> dict[str, Any]:
    from aethos_core.runtime_reconciliation.runtime import assess_runtime_reconciliation

    return assess_runtime_reconciliation()


@router.get("/runtime-reconciliation/patience")
def runtime_reconciliation_patience_api() -> dict[str, Any]:
    from aethos_core.operational_patience.runtime import assess_operational_patience

    return assess_operational_patience()


@router.get("/runtime-reconciliation/decay")
def runtime_reconciliation_decay_api() -> dict[str, Any]:
    from aethos_core.runtime_decay.runtime import assess_runtime_decay

    return assess_runtime_decay()


@router.get("/runtime-reconciliation/verification-windows")
def runtime_reconciliation_windows_api() -> dict[str, Any]:
    from aethos_core.sustained_verification_windows.runtime import assess_sustained_verification_windows

    return assess_sustained_verification_windows()


@router.get("/runtime-reconciliation/recovery-truth")
def runtime_reconciliation_recovery_truth_api() -> dict[str, Any]:
    from aethos_core.recovery_truth_convergence.runtime import assess_recovery_truth_convergence

    return assess_recovery_truth_convergence()


@router.get("/reality-harness-v41/scenarios")
def reality_harness_v41_scenarios_api() -> dict[str, Any]:
    from aethos_core.reality_harness_v41.harness_runtime import harness_state

    return harness_state()


@router.get("/runtime-truth-convergence/state")
def runtime_truth_convergence_state_api() -> dict[str, Any]:
    from aethos_core.runtime_truth_convergence.runtime import assess_runtime_truth_convergence

    return assess_runtime_truth_convergence()


@router.get("/runtime-truth-convergence/stability-windows")
def runtime_truth_stability_windows_api() -> dict[str, Any]:
    from aethos_core.operational_stability_windows.runtime import assess_operational_stability_windows

    return assess_operational_stability_windows()


@router.get("/runtime-truth-convergence/recovery")
def runtime_truth_recovery_convergence_api() -> dict[str, Any]:
    from aethos_core.recovery_convergence.runtime import assess_recovery_convergence

    return assess_recovery_convergence()


@router.get("/runtime-truth-convergence/adaptive-verification")
def runtime_truth_adaptive_verification_api() -> dict[str, Any]:
    from aethos_core.adaptive_sustained_verification.runtime import assess_adaptive_sustained_verification

    return assess_adaptive_sustained_verification()


@router.get("/runtime-truth-convergence/long-tail-decay")
def runtime_truth_long_tail_decay_api() -> dict[str, Any]:
    from aethos_core.long_tail_operational_decay.runtime import assess_long_tail_operational_decay

    return assess_long_tail_operational_decay()


@router.get("/runtime-convergence-cognition/state")
def runtime_convergence_cognition_state_api() -> dict[str, Any]:
    from aethos_core.runtime_convergence_cognition.runtime import assess_runtime_convergence_cognition

    return assess_runtime_convergence_cognition()


@router.get("/runtime-convergence-cognition/infrastructure-intuition")
def runtime_convergence_infrastructure_intuition_api() -> dict[str, Any]:
    from aethos_core.infrastructure_intuition.runtime import assess_infrastructure_intuition

    return assess_infrastructure_intuition()


@router.get("/runtime-convergence-cognition/temporal-confidence")
def runtime_convergence_temporal_confidence_api() -> dict[str, Any]:
    from aethos_core.temporal_confidence.runtime import assess_temporal_confidence

    return assess_temporal_confidence()


@router.get("/runtime-convergence-cognition/kubernetes")
def runtime_convergence_kubernetes_api() -> dict[str, Any]:
    from aethos_core.kubernetes_convergence.runtime import assess_kubernetes_convergence

    return assess_kubernetes_convergence()


@router.get("/runtime-convergence-cognition/replay-continuity")
def runtime_convergence_replay_continuity_api() -> dict[str, Any]:
    from aethos_core.replay_continuity_intelligence.runtime import assess_replay_continuity_intelligence

    return assess_replay_continuity_intelligence()


@router.get("/runtime-convergence-cognition/operational-memory")
def runtime_convergence_operational_memory_api() -> dict[str, Any]:
    from aethos_core.long_tail_operational_memory.runtime import assess_long_tail_operational_memory

    return assess_long_tail_operational_memory()


@router.get("/reality-harness-v42/scenarios")
def reality_harness_v42_scenarios_api() -> dict[str, Any]:
    from aethos_core.reality_harness_v42.harness_runtime import harness_state

    return harness_state()


@router.get("/recovery-continuity-intelligence/state")
def recovery_continuity_intelligence_state_api() -> dict[str, Any]:
    from aethos_core.recovery_continuity.runtime import assess_recovery_continuity_intelligence

    return assess_recovery_continuity_intelligence()


@router.get("/recovery-continuity-intelligence/temporal-trust")
def recovery_continuity_temporal_trust_api() -> dict[str, Any]:
    from aethos_core.temporal_operational_trust.runtime import assess_temporal_operational_trust

    return assess_temporal_operational_trust()


@router.get("/recovery-continuity-intelligence/infrastructure-convergence")
def recovery_continuity_infrastructure_convergence_api() -> dict[str, Any]:
    from aethos_core.infrastructure_convergence.runtime import assess_infrastructure_convergence

    return assess_infrastructure_convergence()


@router.get("/recovery-continuity-intelligence/replay-persistence")
def recovery_continuity_replay_persistence_api() -> dict[str, Any]:
    from aethos_core.replay_persistence.runtime import assess_replay_persistence_intelligence

    return assess_replay_persistence_intelligence()


@router.get("/recovery-continuity-intelligence/adaptive-verification")
def recovery_continuity_adaptive_verification_api() -> dict[str, Any]:
    from aethos_core.adaptive_runtime_verification.runtime import assess_adaptive_runtime_verification

    return assess_adaptive_runtime_verification()


@router.get("/recovery-continuity-intelligence/long-tail-stability")
def recovery_continuity_long_tail_stability_api() -> dict[str, Any]:
    from aethos_core.long_tail_stability.runtime import assess_long_tail_stability

    return assess_long_tail_stability()


@router.get("/recovery-continuity-intelligence/topology-resilience")
def recovery_continuity_topology_resilience_api() -> dict[str, Any]:
    from aethos_core.infrastructure_convergence.topology_resilience import assess_topology_resilience

    return assess_topology_resilience()


@router.get("/recovery-continuity-intelligence/recovery-memory")
def recovery_continuity_recovery_memory_api() -> dict[str, Any]:
    from aethos_core.recovery_continuity.continuity_memory import record_continuity_memory

    return {"ok": True, **record_continuity_memory(stable=True)}


@router.get("/operational-resilience-cognition/state")
def operational_resilience_cognition_state_api() -> dict[str, Any]:
    from aethos_core.operational_resilience_cognition.runtime import assess_operational_resilience_cognition

    return assess_operational_resilience_cognition()


@router.get("/operational-resilience-cognition/infrastructure-fragility")
def operational_resilience_fragility_api() -> dict[str, Any]:
    from aethos_core.infrastructure_fragility.runtime import assess_infrastructure_fragility

    return assess_infrastructure_fragility()


@router.get("/operational-resilience-cognition/temporal-trust")
def operational_resilience_temporal_trust_api() -> dict[str, Any]:
    from aethos_core.temporal_trust_evolution.runtime import assess_temporal_trust_evolution

    return assess_temporal_trust_evolution()


@router.get("/operational-resilience-cognition/kubernetes-resilience")
def operational_resilience_kubernetes_api() -> dict[str, Any]:
    from aethos_core.kubernetes_resilience.runtime import assess_kubernetes_resilience

    return assess_kubernetes_resilience()


@router.get("/operational-resilience-cognition/replay-resilience")
def operational_resilience_replay_api() -> dict[str, Any]:
    from aethos_core.replay_resilience_intelligence.runtime import assess_replay_resilience_intelligence

    return assess_replay_resilience_intelligence()


@router.get("/operational-resilience-cognition/long-tail-stability")
def operational_resilience_long_tail_api() -> dict[str, Any]:
    from aethos_core.long_tail_stability.runtime import assess_long_tail_stability

    return assess_long_tail_stability()


@router.get("/operational-resilience-cognition/recovery-durability")
def operational_resilience_recovery_durability_api() -> dict[str, Any]:
    from aethos_core.operational_resilience_cognition.resilience_trajectories import track_resilience_trajectories

    return {"ok": True, **track_resilience_trajectories()}


@router.get("/operational-resilience-cognition/resilience-memory")
def operational_resilience_memory_api() -> dict[str, Any]:
    from aethos_core.long_tail_resilience_memory.runtime import assess_long_tail_resilience_memory

    return assess_long_tail_resilience_memory()


@router.get("/reality-harness-v43/scenarios")
def reality_harness_v43_scenarios_api() -> dict[str, Any]:
    from aethos_core.reality_harness_v43.harness_runtime import harness_state

    return harness_state()


@router.get("/operational-resilience/state")
def operational_resilience_state_api() -> dict[str, Any]:
    from aethos_core.operational_resilience.runtime import assess_operational_resilience

    return assess_operational_resilience()


@router.get("/operational-resilience/runtime-fragility")
def operational_resilience_runtime_fragility_api() -> dict[str, Any]:
    from aethos_core.runtime_fragility.runtime import assess_runtime_fragility

    return assess_runtime_fragility()


@router.get("/operational-resilience/sustained-trust")
def operational_resilience_sustained_trust_api() -> dict[str, Any]:
    from aethos_core.sustained_trust_evolution.runtime import assess_sustained_trust_evolution

    return assess_sustained_trust_evolution()


@router.get("/operational-resilience/kubernetes-durability")
def operational_resilience_kubernetes_durability_api() -> dict[str, Any]:
    from aethos_core.kubernetes_runtime_durability.runtime import assess_kubernetes_runtime_durability

    return assess_kubernetes_runtime_durability()


@router.get("/operational-resilience/replay-resilience")
def operational_resilience_replay_resilience_api() -> dict[str, Any]:
    from aethos_core.replay_resilience.runtime import assess_replay_resilience_cognition

    return assess_replay_resilience_cognition()


@router.get("/operational-resilience/long-tail-stability")
def operational_resilience_long_tail_api() -> dict[str, Any]:
    from aethos_core.long_tail_stability.runtime import assess_long_tail_stability

    return assess_long_tail_stability()


@router.get("/operational-resilience/recovery-durability")
def operational_resilience_recovery_durability_api() -> dict[str, Any]:
    from aethos_core.operational_resilience.resilience_trajectories import track_operational_resilience_trajectories

    return {"ok": True, **track_operational_resilience_trajectories()}


@router.get("/operational-resilience/resilience-memory")
def operational_resilience_resilience_memory_api() -> dict[str, Any]:
    from aethos_core.long_tail_resilience.runtime import assess_long_tail_resilience

    return assess_long_tail_resilience()


@router.get("/predictive-operational-cognition/state")
def predictive_operational_cognition_state_api() -> dict[str, Any]:
    from aethos_core.predictive_operational_cognition.runtime import assess_predictive_operational_cognition

    return assess_predictive_operational_cognition()


@router.get("/predictive-operational-cognition/fragility-acceleration")
def predictive_fragility_acceleration_api() -> dict[str, Any]:
    from aethos_core.fragility_acceleration.runtime import assess_fragility_acceleration

    return assess_fragility_acceleration()


@router.get("/predictive-operational-cognition/replay-forecasting")
def predictive_replay_forecasting_api() -> dict[str, Any]:
    from aethos_core.replay_erosion_forecasting.runtime import assess_replay_erosion_forecasting

    return assess_replay_erosion_forecasting()


@router.get("/predictive-operational-cognition/topology-forecasting")
def predictive_topology_forecasting_api() -> dict[str, Any]:
    from aethos_core.topology_stability_forecasting.runtime import assess_topology_stability_forecasting

    return assess_topology_stability_forecasting()


@router.get("/predictive-operational-cognition/operational-fatigue")
def predictive_operational_fatigue_api() -> dict[str, Any]:
    from aethos_core.operational_fatigue_intelligence.runtime import assess_operational_fatigue_intelligence

    return assess_operational_fatigue_intelligence()


@router.get("/predictive-operational-cognition/stability-projection")
def predictive_stability_projection_api() -> dict[str, Any]:
    from aethos_core.sustained_stability_forecasting.runtime import assess_sustained_stability_forecasting

    return assess_sustained_stability_forecasting()


@router.get("/predictive-operational-cognition/recovery-forecasting")
def predictive_recovery_forecasting_api() -> dict[str, Any]:
    from aethos_core.predictive_operational_cognition.resilience_projection import project_resilience

    return {"ok": True, **project_resilience()}


@router.get("/predictive-operational-cognition/predictive-memory")
def predictive_memory_api() -> dict[str, Any]:
    from aethos_core.predictive_operational_cognition.predictive_memory import record_predictive_memory

    return {"ok": True, **record_predictive_memory(stable=True)}


@router.get("/reality-harness-v44/scenarios")
def reality_harness_v44_scenarios_api() -> dict[str, Any]:
    from aethos_core.reality_harness_v44.harness_runtime import harness_state

    return harness_state()


@router.get("/runtime-fragility-intelligence/state")
def runtime_fragility_intelligence_state_api() -> dict[str, Any]:
    from aethos_core.runtime_fragility_intelligence.runtime import assess_runtime_fragility_intelligence

    return assess_runtime_fragility_intelligence()


@router.get("/runtime-fragility-intelligence/degradation-acceleration")
def runtime_fragility_degradation_acceleration_api() -> dict[str, Any]:
    from aethos_core.degradation_acceleration.runtime import assess_degradation_acceleration

    return assess_degradation_acceleration()


@router.get("/runtime-fragility-intelligence/replay-erosion")
def runtime_fragility_replay_erosion_api() -> dict[str, Any]:
    from aethos_core.replay_erosion_intelligence.runtime import assess_replay_erosion_intelligence

    return assess_replay_erosion_intelligence()


@router.get("/runtime-fragility-intelligence/topology-fragility")
def runtime_fragility_topology_api() -> dict[str, Any]:
    from aethos_core.topology_fragility_forecasting.runtime import assess_topology_fragility_forecasting

    return assess_topology_fragility_forecasting()


@router.get("/runtime-fragility-intelligence/operational-fatigue")
def runtime_fragility_operational_fatigue_api() -> dict[str, Any]:
    from aethos_core.operational_fatigue_cognition.runtime import assess_operational_fatigue_cognition

    return assess_operational_fatigue_cognition()


@router.get("/runtime-fragility-intelligence/predictive-stability")
def runtime_fragility_predictive_stability_api() -> dict[str, Any]:
    from aethos_core.predictive_runtime_stability.runtime import assess_predictive_runtime_stability

    return assess_predictive_runtime_stability()


@router.get("/runtime-fragility-intelligence/fragility-memory")
def runtime_fragility_memory_api() -> dict[str, Any]:
    from aethos_core.runtime_fragility_intelligence.fragility_memory import record_fragility_history

    return {"ok": True, **record_fragility_history()}


@router.get("/long-tail-operational-forecasting/state")
def long_tail_operational_forecasting_state_api() -> dict[str, Any]:
    from aethos_core.long_tail_operational_forecasting.runtime import assess_long_tail_operational_forecasting

    return assess_long_tail_operational_forecasting()


@router.get("/long-tail-operational-forecasting/operational-survivability")
def long_tail_operational_survivability_api() -> dict[str, Any]:
    from aethos_core.operational_survivability.runtime import assess_operational_survivability

    return assess_operational_survivability()


@router.get("/long-tail-operational-forecasting/replay-longevity")
def long_tail_replay_longevity_api() -> dict[str, Any]:
    from aethos_core.replay_longevity_forecasting.runtime import assess_replay_longevity_forecasting

    return assess_replay_longevity_forecasting()


@router.get("/long-tail-operational-forecasting/topology-sustainability")
def long_tail_topology_sustainability_api() -> dict[str, Any]:
    from aethos_core.topology_sustainability.runtime import assess_topology_sustainability

    return assess_topology_sustainability()


@router.get("/long-tail-operational-forecasting/resilience-exhaustion")
def long_tail_resilience_exhaustion_api() -> dict[str, Any]:
    from aethos_core.resilience_exhaustion.runtime import assess_resilience_exhaustion

    return assess_resilience_exhaustion()


@router.get("/long-tail-operational-forecasting/autonomous-stability")
def long_tail_autonomous_stability_api() -> dict[str, Any]:
    from aethos_core.autonomous_stability_cognition.runtime import assess_autonomous_stability_cognition

    return assess_autonomous_stability_cognition()


@router.get("/long-tail-operational-forecasting/forecasting-memory")
def long_tail_forecasting_memory_api() -> dict[str, Any]:
    from aethos_core.long_tail_operational_forecasting.forecasting_memory import record_forecasting_memory

    return {"ok": True, **record_forecasting_memory(survivable=True)}


@router.get("/reality-harness-v45/scenarios")
def reality_harness_v45_scenarios_api() -> dict[str, Any]:
    from aethos_core.reality_harness_v45.harness_runtime import harness_state

    return harness_state()


@router.get("/long-tail-runtime-cognition/state")
def long_tail_runtime_cognition_state_api() -> dict[str, Any]:
    from aethos_core.long_tail_runtime_cognition.runtime import assess_long_tail_runtime_cognition

    return assess_long_tail_runtime_cognition()


@router.get("/long-tail-runtime-cognition/runtime-survivability")
def long_tail_runtime_survivability_api() -> dict[str, Any]:
    from aethos_core.runtime_survivability_intelligence.runtime import assess_runtime_survivability_intelligence

    return assess_runtime_survivability_intelligence()


@router.get("/long-tail-runtime-cognition/operational-endurance")
def long_tail_operational_endurance_api() -> dict[str, Any]:
    from aethos_core.operational_endurance.runtime import assess_operational_endurance

    return assess_operational_endurance()


@router.get("/long-tail-runtime-cognition/replay-continuity")
def long_tail_replay_continuity_api() -> dict[str, Any]:
    from aethos_core.replay_continuity_survivability.runtime import assess_replay_continuity_survivability

    return assess_replay_continuity_survivability()


@router.get("/long-tail-runtime-cognition/topology-endurance")
def long_tail_topology_endurance_api() -> dict[str, Any]:
    from aethos_core.topology_endurance_forecasting.runtime import assess_topology_endurance_forecasting

    return assess_topology_endurance_forecasting()


@router.get("/long-tail-runtime-cognition/resilience-exhaustion")
def long_tail_resilience_exhaustion_intelligence_api() -> dict[str, Any]:
    from aethos_core.resilience_exhaustion_intelligence.runtime import assess_resilience_exhaustion_intelligence

    return assess_resilience_exhaustion_intelligence()


@router.get("/long-tail-runtime-cognition/cognition-memory")
def long_tail_cognition_memory_api() -> dict[str, Any]:
    from aethos_core.long_tail_runtime_cognition.cognition_memory import record_cognition_memory

    return {"ok": True, **record_cognition_memory()}
