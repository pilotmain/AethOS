# SPDX-License-Identifier: Apache-2.0
"""Production qualification — execution realism tiers."""

from __future__ import annotations

from typing import Any

QUALIFICATION_TIERS = ("alpha", "beta", "stable", "production-reliable", "operationally-trusted")


def assess_production_qualification(
    *,
    deployment: dict[str, Any],
    rollback: dict[str, Any],
    stabilization: dict[str, Any],
    infrastructure: dict[str, Any],
    harness: dict[str, Any],
    decay: dict[str, Any],
    sustained: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sustained = sustained or {}
    checks = {
        "runtime_stabilization_verified": stabilization.get("patience", {}).get("premature_healthy_blocked", True),
        "rollback_integrity_validated": rollback.get("confidence", {}).get("rollback_verified", False),
        "topology_convergence_stable": infrastructure.get("topology", {}).get("converged", False),
        "deployment_truth_reconciled": deployment.get("reality_qualified", False),
        "operational_decay_bounded": decay.get("decay_bounded", True),
        "extended_monitoring_passes": harness.get("verified_count", 0) >= 5,
        "sustained_verification_active": sustained.get("drift_reverification", {}).get("drift_bounded", True),
    }
    passed = sum(1 for v in checks.values() if v)
    if passed >= 7:
        tier = "operationally-trusted"
    elif passed >= 6:
        tier = "production-reliable"
    elif passed >= 4:
        tier = "stable"
    elif passed >= 2:
        tier = "beta"
    else:
        tier = "alpha"
    return {
        "checks": checks,
        "passed_count": passed,
        "total_count": len(checks),
        "qualification_tier": tier,
        "production_reliable": tier in ("production-reliable", "operationally-trusted"),
        "summary": f"Production qualification tier: {tier}.",
    }
