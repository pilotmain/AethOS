# SPDX-License-Identifier: Apache-2.0
"""Operational readiness — production readiness scoring."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix, matrix_summary
from aethos_core.operational_truth.capability_registry import provider_hardening_priority


def assess_operational_readiness() -> dict[str, Any]:
    matrix = build_capability_truth_matrix()
    summary = matrix_summary(matrix)
    tier1 = provider_hardening_priority()
    tier1_registered = sum(1 for p in tier1 if p.get("registered"))
    tier1_score = round(tier1_registered / max(len(tier1), 1) * 100, 1)

    overall = round(
        (summary["average_verification_coverage_pct"] * 0.55)
        + (tier1_score * 0.25)
        + (summary["verified_count"] / max(summary["claimed_count"], 1) * 100 * 0.2),
        1,
    )

    if overall >= 85 and summary["production_ready_count"] >= 3:
        readiness_tier = "production-ready"
    elif overall >= 70:
        readiness_tier = "stable"
    elif overall >= 50:
        readiness_tier = "beta"
    elif overall >= 30:
        readiness_tier = "alpha"
    else:
        readiness_tier = "experimental"

    return {
        "readiness_score": overall,
        "readiness_tier": readiness_tier,
        "verification_coverage_pct": summary["average_verification_coverage_pct"],
        "tier1_hardening_pct": tier1_score,
        "claimed_capabilities": summary["claimed_count"],
        "verified_capabilities": summary["verified_count"],
        "production_ready_capabilities": summary["production_ready_count"],
        "overclaim_risk": summary["overclaim_risk"],
        "summary": (
            f"Operational readiness: {readiness_tier} "
            f"({overall}% composite score, {summary['average_verification_coverage_pct']}% verification coverage)."
        ),
        "tier1_providers": tier1,
    }
