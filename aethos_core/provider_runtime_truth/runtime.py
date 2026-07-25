# SPDX-License-Identifier: Apache-2.0
"""Provider runtime truth aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_runtime_truth.docker_container_recovery import assess_docker_container_recovery
from aethos_core.provider_runtime_truth.github_ci_reconciliation import assess_github_ci_reconciliation
from aethos_core.provider_runtime_truth.kubernetes_rollout_convergence import assess_kubernetes_rollout_convergence
from aethos_core.provider_runtime_truth.provider_runtime_alignment import assess_provider_runtime_alignment
from aethos_core.provider_runtime_truth.railway_runtime_convergence import assess_railway_runtime_convergence
from aethos_core.provider_runtime_truth.vercel_endpoint_convergence import assess_vercel_endpoint_convergence


def assess_provider_runtime_truth() -> dict[str, Any]:
    providers = {
        "railway": assess_railway_runtime_convergence(),
        "github": assess_github_ci_reconciliation(),
        "vercel": assess_vercel_endpoint_convergence(),
        "docker": assess_docker_container_recovery(),
        "kubernetes": assess_kubernetes_rollout_convergence(),
    }
    alignment = {
        "railway": assess_provider_runtime_alignment(provider="railway"),
        "github": assess_provider_runtime_alignment(provider="github", operation_type="workflow_rerun"),
        "vercel": assess_provider_runtime_alignment(provider="vercel", operation_type="redeploy"),
    }
    converged = sum(1 for p in providers.values() if p.get("converged"))
    return {
        "ok": True,
        "providers": providers,
        "alignment": alignment,
        "converged_count": converged,
        "summary": "Provider runtime truth converging toward sustained operational reality.",
    }
