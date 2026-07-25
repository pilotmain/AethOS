# SPDX-License-Identifier: Apache-2.0
"""Execution pressure — repeated failure pressure tracking."""

from __future__ import annotations

from time import time
from typing import Any


def assess_execution_pressure(*, events: list[dict[str, Any]] | None = None, window_minutes: float = 30.0) -> dict[str, Any]:
    """Track repeated failure pressure within a sliding window."""
    cutoff = time() - window_minutes * 60
    rows = [e for e in (events or []) if float(e.get("at") or e.get("created_at") or 0) >= cutoff]

    restarts = sum(1 for e in rows if "restart" in str(e.get("summary", e.get("detail", ""))).lower())
    deploy_fail = sum(1 for e in rows if "deployment" in str(e.get("category", e.get("source", ""))).lower())
    wf_fail = sum(1 for e in rows if "workflow" in str(e.get("category", e.get("source", ""))).lower())

    pressure_score = min(1.0, (restarts + deploy_fail + wf_fail) * 0.15)
    elevated = pressure_score >= 0.45 or restarts >= 3

    return {
        "pressure_score": round(pressure_score, 2),
        "elevated": elevated,
        "restart_count": restarts,
        "deployment_failure_count": deploy_fail,
        "workflow_failure_count": wf_fail,
        "window_minutes": window_minutes,
        "summary": f"Execution pressure {'elevated' if elevated else 'normal'} (score={pressure_score:.2f}).",
    }
