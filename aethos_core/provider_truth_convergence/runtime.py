# SPDX-License-Identifier: Apache-2.0
"""Provider truth convergence aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_hardening.verify import tier1_provider_reliability
from aethos_core.provider_truth_convergence.docker_runtime_truth import assess_docker_runtime_truth
from aethos_core.provider_truth_convergence.github_execution_truth import assess_github_execution_truth
from aethos_core.provider_truth_convergence.kubernetes_rollout_truth import assess_kubernetes_rollout_truth
from aethos_core.provider_truth_convergence.provider_reconciliation import reconcile_provider_reality
from aethos_core.provider_truth_convergence.railway_runtime_truth import assess_railway_runtime_truth
from aethos_core.provider_truth_convergence.rollout_decay import detect_rollout_decay
from aethos_core.provider_truth_convergence.topology_recovery import verify_topology_recovery
from aethos_core.provider_truth_convergence.vercel_runtime_truth import assess_vercel_runtime_truth


def assess_provider_truth_convergence() -> dict[str, Any]:
    providers = {
        "railway": assess_railway_runtime_truth(),
        "github": assess_github_execution_truth(),
        "vercel": assess_vercel_runtime_truth(),
        "docker": assess_docker_runtime_truth(),
        "kubernetes": assess_kubernetes_rollout_truth(),
    }
    reconciliation = {
        "railway": reconcile_provider_reality(provider="railway"),
        "github": reconcile_provider_reality(provider="github", operation_type="workflow_rerun"),
        "vercel": reconcile_provider_reality(provider="vercel", operation_type="redeploy"),
    }
    rollout = detect_rollout_decay()
    topology = verify_topology_recovery()
    tier1 = tier1_provider_reliability()
    converged = sum(
        1
        for p in ("railway", "github", "vercel")
        if providers[p].get("runtime_stabilized")
        or providers[p].get("execution_converged")
        or providers[p].get("runtime_verified")
    )
    return {
        "ok": True,
        "providers": providers,
        "provider_reconciliation": reconciliation,
        "tier1_summary": tier1,
        "rollout_decay": rollout,
        "topology_recovery": topology,
        "converged_count": converged,
        "summary": "Tier 1 provider truth converging toward sustained operational truth.",
    }
