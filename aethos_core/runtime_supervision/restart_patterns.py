# SPDX-License-Identifier: Apache-2.0
"""Restart patterns — instability detection."""

from __future__ import annotations

from typing import Any


def detect_restart_patterns(*, runtime_snapshot: dict[str, Any]) -> dict[str, Any]:
    workloads = runtime_snapshot.get("containers") or runtime_snapshot.get("pods") or []
    if not isinstance(workloads, list):
        workloads = []
    loops = [
        w for w in workloads
        if isinstance(w, dict) and (w.get("recovery_loop") or int(w.get("restart_count") or 0) >= 5)
    ]
    return {
        "restart_loops_detected": len(loops),
        "unstable_workloads": [w.get("name") for w in loops],
        "anomaly_escalation": len(loops) >= 2,
        "summary": f"{len(loops)} workloads show restart loop patterns." if loops else "No restart loop patterns detected.",
    }
