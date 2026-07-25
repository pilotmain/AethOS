# SPDX-License-Identifier: Apache-2.0
"""Deployment correlation — healthy vs failed run comparison."""

from __future__ import annotations

from typing import Any


def correlate_deployments(
    *,
    failed: dict[str, Any] | None,
    healthy: dict[str, Any] | None,
    deployments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compare failed deployment against last healthy deployment."""
    changed_files: list[str] = []
    if failed and healthy:
        fc = str(failed.get("commit") or "")
        hc = str(healthy.get("commit") or "")
        if fc and hc and fc != hc:
            changed_files.append(f"commit delta: {hc[:8]} → {fc[:8]}")
    restart_count = 0
    if failed:
        restart_count = int(failed.get("restart_count") or failed.get("restartCount") or 0)
    regression = bool(failed and healthy and failed.get("id") != healthy.get("id"))
    return {
        "failed_deployment": _dep_summary(failed),
        "last_healthy_deployment": _dep_summary(healthy),
        "regression_detected": regression,
        "restart_count": restart_count,
        "changed_signals": changed_files,
        "recent_deployments": [_dep_summary(d) for d in (deployments or [])[:5]],
    }


def _dep_summary(dep: dict[str, Any] | None) -> dict[str, Any]:
    if not dep:
        return {}
    return {
        "id": str(dep.get("id") or "")[:24],
        "state": str(dep.get("state") or "unknown"),
        "target": str(dep.get("target") or dep.get("environment") or "unknown"),
        "branch": str(dep.get("branch") or ""),
        "commit": str(dep.get("commit") or dep.get("commitSha") or "")[:12],
        "created_at": dep.get("created_at") or dep.get("createdAt"),
        "error_message": str(dep.get("error_message") or dep.get("error") or "")[:300],
    }
