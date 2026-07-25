# SPDX-License-Identifier: Apache-2.0
"""Rollout reconciliation — rollout truth verification."""

from __future__ import annotations

from typing import Any


def reconcile_rollout(
    *,
    deployment: dict[str, Any],
    pod_health: dict[str, Any],
    service_mesh: dict[str, Any],
    node_pressure: dict[str, Any],
) -> dict[str, Any]:
    checks: list[dict[str, str]] = []
    if deployment.get("rollout_complete"):
        checks.append({"check": "Deployment updated successfully", "status": "confirmed"})
    if pod_health.get("all_ready"):
        checks.append({"check": "Pod replacement stabilized", "status": "confirmed"})
        checks.append({"check": "Readiness probes recovered", "status": "confirmed"})
    if service_mesh.get("routing_normalized"):
        checks.append({"check": "Service routing normalized", "status": "confirmed"})
    if node_pressure.get("telemetry_within_thresholds"):
        checks.append({"check": "Cluster telemetry within expected thresholds", "status": "confirmed"})
    verified = len(checks) >= 4
    return {
        "verified": verified,
        "checks": checks,
        "verification_coverage_pct": round(len(checks) / 5 * 100),
        "summary": _build_summary(verified, checks),
    }


def _build_summary(verified: bool, checks: list[dict[str, str]]) -> str:
    if not verified:
        return "Rollout reported complete — operational verification incomplete. Extended observation remains active."
    lines = ["Rollout verification confirmed:"]
    for c in checks:
        lines.append(f"- {c['check'].lower()}")
    lines.append("")
    lines.append("Extended observation remains active for reconciliation assurance.")
    return "\n".join(lines)
