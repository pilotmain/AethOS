# SPDX-License-Identifier: Apache-2.0
"""Recovery planner — staged recovery sequencing."""

from __future__ import annotations

from typing import Any


def plan_recovery_sequence(*, topology: dict[str, Any], degraded: list[str]) -> dict[str, Any]:
    critical = topology.get("classifications", {}).get("critical") or []
    stages: list[dict[str, Any]] = []
    if degraded:
        for i, svc in enumerate(degraded[:4]):
            stages.append({"stage": i + 1, "service": svc, "action": "stabilize", "depends_on": critical[:1]})
    else:
        stages = [{"stage": 1, "service": "runtime", "action": "observe", "depends_on": []}]
    return {
        "stages": stages,
        "stage_count": len(stages),
        "summary": f"Recovery plan: {len(stages)} staged stabilization sequence(s).",
    }
