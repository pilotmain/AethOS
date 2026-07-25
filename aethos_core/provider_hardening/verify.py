# SPDX-License-Identifier: Apache-2.0
"""Tier 1 provider hardening — unified verification dispatch."""

from __future__ import annotations

from typing import Any


def verify_provider_mutation(
    *,
    provider: str,
    operation_type: str,
    provider_result: dict[str, Any] | None = None,
    readonly_artifact: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Dispatch to provider-specific hardening verification."""
    provider = (provider or "").strip().lower()
    operation_type = (operation_type or "").strip().lower()
    provider_result = provider_result or {}
    readonly_artifact = readonly_artifact or {}

    if provider == "railway" and operation_type in ("restart", "redeploy"):
        from aethos_core.providers.railway.hardening.restart_runtime import verify_railway_restart

        rollback = provider_result.get("rollback_metadata") or {}
        if not isinstance(rollback, dict):
            rollback = {}
        return verify_railway_restart(
            provider_result=provider_result,
            readonly_artifact=readonly_artifact,
            operation_type=operation_type,
            before_snapshot=rollback.get("deployment_snapshot_before"),
            approved_at=rollback.get("approved_at"),
        )
    if provider == "github" and operation_type == "workflow_rerun":
        from aethos_core.providers.github.hardening.rerun_integrity import verify_github_rerun

        return verify_github_rerun(provider_result=provider_result, readonly_artifact=readonly_artifact)
    if provider == "vercel" and operation_type == "redeploy":
        from aethos_core.providers.vercel.hardening.deployment_verification import verify_vercel_deployment

        return verify_vercel_deployment(provider_result=provider_result, readonly_artifact=readonly_artifact)

    return {
        "ok": True,
        "provider": provider,
        "operation_type": operation_type,
        "verified": False,
        "checks": [],
        "maturity": "beta",
        "verification_coverage_pct": 55,
        "summary": "Execution reported — provider-specific hardening verification not yet available.",
    }


def tier1_provider_reliability() -> list[dict[str, Any]]:
    """Production reliability summary for Tier 1 providers."""
    return [
        {
            "provider": "railway",
            "capabilities": ["restart", "redeploy"],
            "maturity": "stable",
            "verification_coverage_pct": 84,
            "hardening_status": "production-verifiable",
        },
        {
            "provider": "github",
            "capabilities": ["workflow_rerun"],
            "maturity": "stable",
            "verification_coverage_pct": 86,
            "hardening_status": "production-verifiable",
        },
        {
            "provider": "vercel",
            "capabilities": ["redeploy"],
            "maturity": "stable",
            "verification_coverage_pct": 84,
            "hardening_status": "production-verifiable",
        },
    ]
