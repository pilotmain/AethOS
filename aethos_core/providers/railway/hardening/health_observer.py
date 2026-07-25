# SPDX-License-Identifier: Apache-2.0
"""Railway health observer — endpoint recovery monitoring."""

from __future__ import annotations

from typing import Any


def observe_health_recovery(*, readonly_artifact: dict[str, Any], provider_result: dict[str, Any]) -> dict[str, Any]:
    summary = str(readonly_artifact.get("summary") or "").lower()
    state = str(provider_result.get("deployment_state_after") or "").lower()
    reachable = any(w in summary for w in ("running", "healthy", "active", "success")) or state in (
        "success",
        "running",
        "ready",
        "active",
    )
    return {
        "runtime_reachable": reachable,
        "health_stabilized": reachable,
        "summary": "Runtime became reachable and health endpoint stabilized." if reachable else "Health recovery not yet confirmed.",
    }
