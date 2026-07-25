# SPDX-License-Identifier: Apache-2.0
"""Health reconciliation — post-action health recovery checks."""

from __future__ import annotations

from typing import Any


def reconcile_health(*, provider: str, readonly_artifact: dict[str, Any], operation_type: str = "") -> dict[str, Any]:
    summary_text = str(readonly_artifact.get("summary") or "").lower()
    evidence = readonly_artifact.get("evidence") or readonly_artifact.get("items") or []
    state = None
    if isinstance(evidence, list):
        for item in evidence:
            if isinstance(item, dict):
                state = item.get("state") or item.get("status")
                if state:
                    break

    state_str = str(state or "").lower()
    if state_str in ("success", "running", "ready", "active") or any(w in summary_text for w in ("healthy", "success", "running")):
        health = "healthy"
    elif state_str in ("failed", "crashed", "error") or any(w in summary_text for w in ("failed", "error", "unhealthy")):
        health = "unhealthy"
    else:
        health = "unknown"

    stabilized = health == "healthy"
    return {
        "health": health,
        "stabilized": stabilized,
        "provider": provider,
        "operation_type": operation_type,
        "summary": f"Health reconciliation for {provider}: {health}.",
        "checks": [
            {"name": "deployment_state", "ok": stabilized, "detail": str(state or summary_text[:120])},
        ],
    }
