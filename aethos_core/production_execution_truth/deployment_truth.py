# SPDX-License-Identifier: Apache-2.0
"""Deployment truth — deployment reality scoring."""

from __future__ import annotations

from typing import Any

from aethos_core.production_execution_truth.mutation_truth_convergence import converge_mutation_truth


def assess_deployment_truth(*, provider: str = "railway") -> dict[str, Any]:
    convergence = converge_mutation_truth(provider=provider, operation_type="redeploy" if provider == "vercel" else "restart")
    verification = convergence.get("verification") or {}
    score = float(verification.get("verification_coverage_pct") or 70) / 100
    tier = "production-reliable" if score >= 0.85 else "stable" if score >= 0.75 else "beta"
    return {
        "provider": provider,
        "deployment_truth_score": round(score, 2),
        "qualification_tier": tier,
        "convergence": convergence,
        "reality_qualified": score >= 0.75,
        "summary": convergence.get("summary", "Deployment truth assessing."),
    }
