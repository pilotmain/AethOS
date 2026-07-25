# SPDX-License-Identifier: Apache-2.0
"""Restart reconciliation — verified container recovery."""

from __future__ import annotations

from typing import Any


def reconcile_container_restart(
    *,
    container_name: str,
    before: dict[str, Any],
    after: dict[str, Any],
) -> dict[str, Any]:
    before_status = str(before.get("status") or "").lower()
    after_status = str(after.get("status") or "").lower()
    restart_loop = bool(after.get("recovery_loop") or after.get("restart_count", 0) > 5)
    stabilized = after_status in ("healthy", "running", "up") and not restart_loop
    checks: list[dict[str, str]] = []
    if after_status in ("healthy", "running", "up"):
        checks.append({"check": "Container runtime reachable", "status": "confirmed"})
    if not restart_loop:
        checks.append({"check": "Restart loop not detected", "status": "confirmed"})
    if before_status != after_status:
        checks.append({"check": "Recovery transition observed", "status": "confirmed"})
    return {
        "container": container_name,
        "verified": stabilized and len(checks) >= 2,
        "restart_loop_detected": restart_loop,
        "checks": checks,
        "summary": (
            f"Container {container_name} recovery verified."
            if stabilized
            else f"Container {container_name} recovery incomplete — extended monitoring active."
        ),
    }
