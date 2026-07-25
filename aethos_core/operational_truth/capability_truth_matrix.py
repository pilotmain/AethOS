# SPDX-License-Identifier: Apache-2.0
"""Capability truth matrix — claimed vs verified operational maturity."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_truth.capability_registry import list_all_capabilities
from aethos_core.operational_truth.maturity_classification import classify_maturity, tier_label

# Verified maturity baselines — updated as harness scenarios pass
_CAPABILITY_BASELINE: dict[str, dict[str, Any]] = {
    "railway:restart": {
        "real_level": "full",
        "verified_level": "full",
        "verification_coverage": 0.84,
        "prod_ready": False,
    },
    "railway:redeploy": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.78,
        "prod_ready": False,
    },
    # Env-var writes have real executors (railway mutations.execute_railway_set_env_var,
    # vercel mutations_api.upsert_env_var/remove_env_var) + preflight/guard tests, governed by
    # provider_env_var_mutations_enabled. Beta until live-write verification → stable.
    "railway:set_env_var": {
        "real_level": "full",
        "verified_level": "partial",
        "verification_coverage": 0.72,
        "prod_ready": False,
    },
    "vercel:set_env_var": {
        "real_level": "full",
        "verified_level": "partial",
        "verification_coverage": 0.72,
        "prod_ready": False,
    },
    "vercel:remove_env_var": {
        "real_level": "full",
        "verified_level": "partial",
        "verification_coverage": 0.70,
        "prod_ready": False,
    },
    "github:workflow_rerun": {
        "real_level": "full",
        "verified_level": "full",
        "verification_coverage": 0.86,
        "prod_ready": False,
    },
    "github:create_branch": {
        # Real governed executor (git_write_api.create_branch) + unit tests + dry-run path.
        # Beta until a live create→confirm→delete verification promotes it to stable.
        "real_level": "full",
        "verified_level": "partial",
        "verification_coverage": 0.62,
        "prod_ready": False,
    },
    "github:cancel_workflow": {
        # Real governed executor (git_write_api.cancel_workflow: resolve latest active run →
        # POST .../cancel) + unit tests + dry-run. Beta until live-verified.
        "real_level": "full",
        "verified_level": "partial",
        "verification_coverage": 0.62,
        "prod_ready": False,
    },
    "github:redeploy": {
        # Real governed executor (git_write_api.redeploy: re-run latest workflow run) + tests.
        "real_level": "full",
        "verified_level": "partial",
        "verification_coverage": 0.60,
        "prod_ready": False,
    },
    "vercel:restart": {
        # Serverless has no restart; honest alias to the real redeploy executor + tests.
        "real_level": "full",
        "verified_level": "partial",
        "verification_coverage": 0.62,
        "prod_ready": False,
    },
    # ── Destructive write-ops: real governed executors + unit tests + dry-run/preflight.
    # Beta — they reach stable only after an approved live end-to-end verification.
    "github:commit_changes": {
        "real_level": "full",
        "verified_level": "partial",
        "verification_coverage": 0.60,
        "prod_ready": False,
    },
    "github:push_branch": {
        "real_level": "full",
        "verified_level": "partial",
        "verification_coverage": 0.58,
        "prod_ready": False,
    },
    "github:open_pr": {
        "real_level": "full",
        "verified_level": "partial",
        "verification_coverage": 0.60,
        "prod_ready": False,
    },
    "vercel:rollback": {
        "real_level": "full",
        "verified_level": "partial",
        "verification_coverage": 0.58,
        "prod_ready": False,
    },
    "vercel:promote_deployment": {
        "real_level": "full",
        "verified_level": "partial",
        "verification_coverage": 0.58,
        "prod_ready": False,
    },
    "vercel:deploy_from_git": {
        "real_level": "full",
        "verified_level": "partial",
        "verification_coverage": 0.58,
        "prod_ready": False,
    },
    "vercel:redeploy": {
        "real_level": "full",
        "verified_level": "full",
        "verification_coverage": 0.84,
        "prod_ready": False,
    },
    "browser_evidence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.82,
        "prod_ready": False,
    },
    "telegram_research": {
        "real_level": "full",
        "verified_level": "partial",
        "verification_coverage": 0.64,
        "prod_ready": False,
    },
    "sandbox_execution": {
        "real_level": "partial",
        "verified_level": "none",
        "verification_coverage": 0.35,
        "prod_ready": False,
    },
    "replay_reconstruction": {
        "real_level": "partial",
        "verified_level": "partial",
        "verification_coverage": 0.6,
        "prod_ready": False,
    },
    "engineering_execution": {
        "real_level": "partial",
        "verified_level": "partial",
        "verification_coverage": 0.72,
        "prod_ready": False,
    },
    "mutation_reconciliation": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.8,
        "prod_ready": False,
    },
    "rollback_verification": {
        "real_level": "partial",
        "verified_level": "partial",
        "verification_coverage": 0.68,
        "prod_ready": False,
    },
    "docker_container_intelligence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.82,
        "prod_ready": False,
    },
    "kubernetes_runtime_intelligence": {
        "real_level": "full",
        "verified_level": "full",
        "verification_coverage": 0.84,
        "prod_ready": False,
    },
    "topology_intelligence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.80,
        "prod_ready": False,
    },
    "infrastructure_reconciliation": {
        "real_level": "partial",
        "verified_level": "partial",
        "verification_coverage": 0.72,
        "prod_ready": False,
    },
    "runtime_supervision": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.78,
        "prod_ready": False,
    },
    "infrastructure_confidence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.76,
        "prod_ready": False,
    },
    "continuous_verification": {
        "real_level": "full",
        "verified_level": "full",
        "verification_coverage": 0.86,
        "prod_ready": False,
    },
    "recovery_orchestration": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.82,
        "prod_ready": False,
    },
    "drift_intelligence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.80,
        "prod_ready": False,
    },
    "predictive_operations": {
        "real_level": "partial",
        "verified_level": "partial",
        "verification_coverage": 0.74,
        "prod_ready": False,
    },
    "production_confidence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.84,
        "prod_ready": False,
    },
    "reliability_memory": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.78,
        "prod_ready": False,
    },
    "conversational_synthesis": {
        "real_level": "full",
        "verified_level": "full",
        "verification_coverage": 0.88,
        "prod_ready": False,
    },
    "human_trust_presentation": {
        "real_level": "full",
        "verified_level": "full",
        "verification_coverage": 0.90,
        "prod_ready": False,
    },
    "presentation_safety": {
        "real_level": "full",
        "verified_level": "full",
        "verification_coverage": 0.92,
        "prod_ready": False,
    },
    "recommendation_intelligence": {
        "real_level": "full",
        "verified_level": "full",
        "verification_coverage": 0.86,
        "prod_ready": False,
    },
    "conversational_elegance": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.84,
        "prod_ready": False,
    },
    "conversational_reliability": {
        "real_level": "full",
        "verified_level": "full",
        "verification_coverage": 0.90,
        "prod_ready": False,
    },
    "intent_reliability": {
        "real_level": "full",
        "verified_level": "full",
        "verification_coverage": 0.92,
        "prod_ready": False,
    },
    "presentation_integrity": {
        "real_level": "full",
        "verified_level": "full",
        "verification_coverage": 0.94,
        "prod_ready": False,
    },
    "recommendation_refinement": {
        "real_level": "full",
        "verified_level": "full",
        "verification_coverage": 0.89,
        "prod_ready": False,
    },
    "human_trust_language": {
        "real_level": "full",
        "verified_level": "full",
        "verification_coverage": 0.91,
        "prod_ready": False,
    },
    "conversational_convergence": {
        "real_level": "full",
        "verified_level": "full",
        "verification_coverage": 0.92,
        "prod_ready": False,
    },
    "interaction_layers": {
        "real_level": "full",
        "verified_level": "full",
        "verification_coverage": 0.90,
        "prod_ready": False,
    },
    "conversational_qualification": {
        "real_level": "full",
        "verified_level": "full",
        "verification_coverage": 0.93,
        "prod_ready": False,
    },
    "production_execution_truth": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.82,
        "prod_ready": False,
    },
    "provider_truth_convergence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.84,
        "prod_ready": False,
    },
    "rollback_integrity": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.80,
        "prod_ready": False,
    },
    "runtime_stabilization_intelligence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.81,
        "prod_ready": False,
    },
    "infrastructure_truth": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.83,
        "prod_ready": False,
    },
    "reality_harness_v4": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.81,
        "prod_ready": False,
    },
    "sustained_verification": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.84,
        "prod_ready": False,
    },
    "production_execution_realism": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.85,
        "prod_ready": False,
    },
    "runtime_reconciliation": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.86,
        "prod_ready": False,
    },
    "operational_patience_intelligence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.87,
        "prod_ready": False,
    },
    "runtime_decay_intelligence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.84,
        "prod_ready": False,
    },
    "provider_runtime_truth": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.85,
        "prod_ready": False,
    },
    "sustained_verification_windows": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.86,
        "prod_ready": False,
    },
    "recovery_truth_convergence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.83,
        "prod_ready": False,
    },
    "reality_harness_v41": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.85,
        "prod_ready": False,
    },
    "runtime_truth_convergence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.88,
        "prod_ready": False,
    },
    "operational_stability_windows": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.87,
        "prod_ready": False,
    },
    "recovery_convergence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.86,
        "prod_ready": False,
    },
    "long_tail_operational_decay": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.85,
        "prod_ready": False,
    },
    "adaptive_sustained_verification": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.87,
        "prod_ready": False,
    },
    "runtime_convergence_cognition": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.89,
        "prod_ready": False,
    },
    "infrastructure_intuition": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.86,
        "prod_ready": False,
    },
    "temporal_confidence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.87,
        "prod_ready": False,
    },
    "kubernetes_convergence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.84,
        "prod_ready": False,
    },
    "replay_continuity_intelligence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.86,
        "prod_ready": False,
    },
    "long_tail_operational_memory": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.85,
        "prod_ready": False,
    },
    "reality_harness_v42": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.87,
        "prod_ready": False,
    },
    "recovery_continuity_intelligence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.90,
        "prod_ready": False,
    },
    "temporal_operational_trust": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.88,
        "prod_ready": False,
    },
    "infrastructure_convergence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.87,
        "prod_ready": False,
    },
    "replay_persistence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.86,
        "prod_ready": False,
    },
    "adaptive_runtime_verification": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.88,
        "prod_ready": False,
    },
    "long_tail_stability": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.85,
        "prod_ready": False,
    },
    "operational_resilience_cognition": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.91,
        "prod_ready": False,
    },
    "infrastructure_fragility": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.87,
        "prod_ready": False,
    },
    "temporal_trust_evolution": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.89,
        "prod_ready": False,
    },
    "kubernetes_resilience": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.86,
        "prod_ready": False,
    },
    "replay_resilience_intelligence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.88,
        "prod_ready": False,
    },
    "long_tail_resilience_memory": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.86,
        "prod_ready": False,
    },
    "reality_harness_v43": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.88,
        "prod_ready": False,
    },
    "operational_resilience": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.92,
        "prod_ready": False,
    },
    "runtime_fragility": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.88,
        "prod_ready": False,
    },
    "sustained_trust_evolution": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.90,
        "prod_ready": False,
    },
    "kubernetes_runtime_durability": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.87,
        "prod_ready": False,
    },
    "replay_resilience": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.89,
        "prod_ready": False,
    },
    "long_tail_resilience": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.87,
        "prod_ready": False,
    },
    "predictive_operational_cognition": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.93,
        "prod_ready": False,
    },
    "fragility_acceleration": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.89,
        "prod_ready": False,
    },
    "replay_erosion_forecasting": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.88,
        "prod_ready": False,
    },
    "topology_stability_forecasting": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.87,
        "prod_ready": False,
    },
    "operational_fatigue_intelligence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.88,
        "prod_ready": False,
    },
    "sustained_stability_forecasting": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.90,
        "prod_ready": False,
    },
    "reality_harness_v44": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.89,
        "prod_ready": False,
    },
    "runtime_fragility_intelligence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.94,
        "prod_ready": False,
    },
    "degradation_acceleration": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.90,
        "prod_ready": False,
    },
    "replay_erosion_intelligence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.89,
        "prod_ready": False,
    },
    "topology_fragility_forecasting": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.88,
        "prod_ready": False,
    },
    "operational_fatigue_cognition": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.89,
        "prod_ready": False,
    },
    "predictive_runtime_stability": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.91,
        "prod_ready": False,
    },
    "long_tail_operational_forecasting": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.92,
        "prod_ready": False,
    },
    "operational_survivability": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.90,
        "prod_ready": False,
    },
    "replay_longevity_forecasting": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.91,
        "prod_ready": False,
    },
    "topology_sustainability": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.89,
        "prod_ready": False,
    },
    "resilience_exhaustion": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.90,
        "prod_ready": False,
    },
    "autonomous_stability_cognition": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.91,
        "prod_ready": False,
    },
    "reality_harness_v45": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.90,
        "prod_ready": False,
    },
    "long_tail_runtime_cognition": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.92,
        "prod_ready": False,
    },
    "runtime_survivability_intelligence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.91,
        "prod_ready": False,
    },
    "operational_endurance": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.90,
        "prod_ready": False,
    },
    "replay_continuity_survivability": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.91,
        "prod_ready": False,
    },
    "topology_endurance_forecasting": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.89,
        "prod_ready": False,
    },
    "resilience_exhaustion_intelligence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.90,
        "prod_ready": False,
    },
    "conversational_operational_grounding": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.92,
        "prod_ready": False,
    },
    "continuity_reconstruction": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.91,
        "prod_ready": False,
    },
    "operational_context_memory": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.90,
        "prod_ready": False,
    },
    "governance_restraint_runtime": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.93,
        "prod_ready": False,
    },
    "conversational_realism": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.92,
        "prod_ready": False,
    },
    "telegram_session_persistence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.90,
        "prod_ready": False,
    },
    "operational_partner_presence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.91,
        "prod_ready": False,
    },
    "operational_thread_integrity": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.91,
        "prod_ready": False,
    },
    "conversational_realism_polish": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.92,
        "prod_ready": False,
    },
    "cross_surface_reality_convergence": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.91,
        "prod_ready": False,
    },
    "live_operational_grounding": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.90,
        "prod_ready": False,
    },
    "operational_entity_runtime": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.88,
        "prod_ready": False,
    },
    "operational_progression_runtime": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.87,
        "prod_ready": False,
    },
    "investigative_continuity_runtime": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.86,
        "prod_ready": False,
    },
    "durable_agent_jobs_runtime": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.85,
        "prod_ready": False,
    },
    "job_truth_runtime": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.84,
        "prod_ready": False,
    },
    "telegram_validation_harness": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.83,
        "prod_ready": False,
    },
    "external_execution_truth_runtime": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.82,
        "prod_ready": False,
    },
    "telegram_soak_runtime": {
        "real_level": "full",
        "verified_level": "mostly",
        "verification_coverage": 0.81,
        "prod_ready": False,
    },
}


def _baseline_for(cap_id: str) -> dict[str, Any]:
    return _CAPABILITY_BASELINE.get(
        cap_id,
        {"real_level": "unknown", "verified_level": "none", "verification_coverage": 0.0, "prod_ready": False},
    )


def build_capability_truth_matrix() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cap in list_all_capabilities():
        cap_id = str(cap["id"])
        baseline = _baseline_for(cap_id)
        claimed = bool(cap.get("claimed"))
        real_level = str(baseline["real_level"])
        verified_level = str(baseline["verified_level"])
        coverage = float(baseline["verification_coverage"])
        prod_ready = bool(baseline["prod_ready"])
        maturity = classify_maturity(
            claimed=claimed,
            real_level=real_level,
            verified_level=verified_level,
            verification_coverage=coverage,
            prod_ready=prod_ready,
        )
        rows.append({
            **cap,
            "claimed": claimed,
            "real": real_level,
            "verified": verified_level,
            "verification_coverage_pct": round(coverage * 100),
            "prod_ready": prod_ready,
            "maturity": maturity,
            "maturity_label": tier_label(maturity),
            "honest_summary": _honest_summary(cap_id, claimed, real_level, verified_level, maturity),
        })
    return rows


def _honest_summary(cap_id: str, claimed: bool, real: str, verified: str, maturity: str) -> str:
    if not claimed:
        return "Not claimed — capability disabled or unavailable."
    if maturity == "production-ready":
        return "Operationally verified under real conditions."
    if verified in ("none", "unknown") and real == "partial":
        return "Partial substrate — end-to-end verification incomplete."
    if verified == "partial":
        return "Partially verified — extended operational validation recommended."
    if verified == "mostly":
        return "Mostly verified — near production-ready with remaining coverage gaps."
    return f"Claimed capability with {real} real substrate and {verified} verification."


def matrix_summary(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    claimed = [r for r in matrix if r.get("claimed")]
    verified = [r for r in claimed if r.get("verified") in ("partial", "mostly", "full")]
    prod = [r for r in matrix if r.get("prod_ready")]
    avg_coverage = round(
        sum(r.get("verification_coverage_pct", 0) for r in claimed) / max(len(claimed), 1),
        1,
    )
    return {
        "total_capabilities": len(matrix),
        "claimed_count": len(claimed),
        "verified_count": len(verified),
        "production_ready_count": len(prod),
        "average_verification_coverage_pct": avg_coverage,
        "overclaim_risk": any(
            r.get("claimed") and r.get("verified") in ("none", "unknown") and r.get("real") == "partial"
            for r in matrix
        ),
    }
