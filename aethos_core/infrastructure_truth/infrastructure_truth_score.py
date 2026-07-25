# SPDX-License-Identifier: Apache-2.0
"""Infrastructure truth score — bounded trust scoring."""

from __future__ import annotations

from typing import Any


def score_infrastructure_truth(*, cluster: dict[str, Any], topology: dict[str, Any], pods: dict[str, Any]) -> dict[str, Any]:
    score = 0.0
    if cluster.get("cluster_stable"):
        score += 0.35
    if topology.get("converged"):
        score += 0.25
    if pods.get("recovery_integrity", 0) >= 0.8:
        score += 0.25
    score += 0.15  # baseline infrastructure awareness
    tier = "production-reliable" if score >= 0.85 else "stable" if score >= 0.7 else "beta"
    return {
        "infrastructure_truth_score": round(min(1.0, score), 2),
        "qualification_tier": tier,
        "summary": f"Infrastructure truth scored at {round(score * 100)}% — {tier}.",
    }
