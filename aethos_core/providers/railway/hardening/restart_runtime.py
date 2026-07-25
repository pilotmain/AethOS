# SPDX-License-Identifier: Apache-2.0
"""Railway restart runtime — governed restart lifecycle with production verification."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.hardening.deployment_correlation import correlate_deployment_signals
from aethos_core.providers.railway.hardening.deployment_truth import assess_deployment_truth
from aethos_core.providers.railway.hardening.health_observer import observe_health_recovery
from aethos_core.providers.railway.hardening.recovery_verification import verify_recovery_stabilization
from aethos_core.providers.railway.hardening.telemetry_integrity import assess_telemetry_integrity


def verify_railway_restart(
    *,
    provider_result: dict[str, Any] | None = None,
    readonly_artifact: dict[str, Any] | None = None,
    operation_type: str = "restart",
    before_snapshot: dict[str, Any] | None = None,
    approved_at: str | float | None = None,
) -> dict[str, Any]:
    """Production-verifiable Railway restart/redeploy outcome."""
    provider_result = provider_result or {}
    readonly_artifact = readonly_artifact or {}

    rollback = provider_result.get("rollback_metadata") or {}
    if not isinstance(rollback, dict):
        rollback = {}
    snapshot_before = before_snapshot or rollback.get("deployment_snapshot_before")
    service_id = str(
        provider_result.get("service_id")
        or rollback.get("service_id")
        or (snapshot_before or {}).get("service_id")
        or ""
    )

    restart_verification: dict[str, Any] | None = None
    if isinstance(snapshot_before, dict) and service_id:
        from aethos_core.providers.railway.hardening.restart_transition import verify_railway_restart_transition

        restart = verify_railway_restart_transition(
            service_id=service_id,
            before_snapshot=snapshot_before,
            approved_at=approved_at or rollback.get("approved_at"),
            provider_result=provider_result,
            readonly_artifact=readonly_artifact,
            provider_request_accepted=bool(provider_result.get("ok")),
        )
        restart_verification = restart.to_dict()

    deployment_truth = assess_deployment_truth(
        provider_result=provider_result,
        readonly_artifact=readonly_artifact,
        before_snapshot=snapshot_before if isinstance(snapshot_before, dict) else None,
        approved_at=approved_at or rollback.get("approved_at"),
    )
    health = observe_health_recovery(readonly_artifact=readonly_artifact, provider_result=provider_result)
    telemetry = assess_telemetry_integrity(readonly_artifact=readonly_artifact)
    browser_verified = bool(readonly_artifact.get("browser_evidence") or provider_result.get("browser_verified"))
    correlation = correlate_deployment_signals(
        deployment_truth=deployment_truth,
        health=health,
        telemetry=telemetry,
        browser_verified=browser_verified,
    )
    recovery = verify_recovery_stabilization(deployment_truth=deployment_truth, health=health, telemetry=telemetry)

    checks: list[dict[str, str]] = []
    if restart_verification:
        checks.extend(restart_verification.get("checks") or [])
    elif deployment_truth.get("transition_detected"):
        checks.append({"check": "New deployment transition detected", "status": "confirmed", "detail": str(deployment_truth.get("state_after") or "")})
    if health.get("runtime_reachable"):
        checks.append({"check": "Runtime became reachable", "status": "confirmed", "detail": health.get("summary", "")})
    if health.get("health_stabilized"):
        checks.append({"check": "Health endpoint stabilized", "status": "confirmed", "detail": ""})
    if telemetry.get("freshness_recovered"):
        checks.append({"check": "Telemetry freshness recovered", "status": "confirmed", "detail": telemetry.get("summary", "")})
    if browser_verified:
        checks.append({"check": "Browser verification completed", "status": "confirmed", "detail": ""})

    if restart_verification:
        verified = bool(restart_verification.get("verified"))
        transition_detected = bool(restart_verification.get("transition_detected"))
    else:
        verified = bool(deployment_truth.get("transition_detected")) and bool(health.get("runtime_reachable"))
        transition_detected = bool(deployment_truth.get("transition_detected"))

    summary = _build_summary(
        operation_type,
        verified,
        checks,
        recovery.get("extended_monitoring_recommended", True),
        restart_verification=restart_verification,
        transition_detected=transition_detected,
    )

    return {
        "ok": True,
        "provider": "railway",
        "operation_type": operation_type,
        "verified": verified,
        "checks": checks,
        "deployment_truth": deployment_truth,
        "health": health,
        "telemetry": telemetry,
        "correlation": correlation,
        "recovery": recovery,
        "restart_verification": restart_verification,
        "transition_detected": transition_detected,
        "verification_coverage_pct": round(float(correlation.get("correlation_score", 0)) * 100),
        "maturity": "stable" if verified else "beta",
        "summary": summary,
    }


def _build_summary(
    operation: str,
    verified: bool,
    checks: list[dict[str, str]],
    extended_monitoring: bool,
    *,
    restart_verification: dict[str, Any] | None = None,
    transition_detected: bool = False,
) -> str:
    label = "Restart" if operation == "restart" else "Deployment"
    if restart_verification and restart_verification.get("summary"):
        base = str(restart_verification["summary"])
        if verified:
            lines = [base, "", "Operational verification confirmed:"]
            for c in checks:
                lines.append(f"- {c['check'].lower()}")
            lines.append("")
            lines.append("Extended monitoring remains active for stabilization assurance.")
            return "\n".join(lines)
        if restart_verification.get("state") == "service_online_but_restart_unproven":
            return (
                f"{base}\n\n"
                "I'm treating the restart as unverified rather than confirmed."
            )
        return (
            f"{base}\n\n"
            "Operational verification is incomplete — extended monitoring remains active for stabilization assurance."
        )
    if not verified:
        if transition_detected:
            return (
                f"{label} transition detected, but service recovery is not fully confirmed.\n\n"
                "Operational verification is incomplete — extended monitoring remains active for stabilization assurance."
            )
        return (
            f"{label} request completed.\n\n"
            "Operational verification is incomplete — extended monitoring remains active for stabilization assurance."
        )
    lines = [f"{label} request completed.", "", "Operational verification confirmed:"]
    for c in checks:
        lines.append(f"- {c['check'].lower()}")
    lines.append("")
    lines.append("Extended monitoring remains active for stabilization assurance.")
    return "\n".join(lines)
