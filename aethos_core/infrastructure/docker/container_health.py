# SPDX-License-Identifier: Apache-2.0
"""Container health — health + restart verification."""

from __future__ import annotations

from typing import Any


def assess_container_health(*, containers: list[dict[str, Any]]) -> dict[str, Any]:
    healthy = [c for c in containers if str(c.get("status", "")).lower() in ("healthy", "running", "up")]
    degraded = [c for c in containers if str(c.get("status", "")).lower() in ("recovering", "unhealthy", "restarting")]
    return {
        "healthy_count": len(healthy),
        "degraded_count": len(degraded),
        "healthy": healthy,
        "degraded": degraded,
        "all_healthy": len(degraded) == 0 and len(healthy) > 0,
        "summary": (
            f"{len(healthy)} containers healthy, {len(degraded)} degraded."
            if degraded
            else f"All {len(healthy)} containers report healthy runtime state."
        ),
    }
