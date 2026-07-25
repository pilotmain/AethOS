# SPDX-License-Identifier: Apache-2.0
"""Topology recovery — cascading recovery analysis."""

from __future__ import annotations

from typing import Any


def analyze_topology_recovery(*, propagation: dict[str, Any], supervision: dict[str, Any]) -> dict[str, Any]:
    impacted = propagation.get("potentially_impacted") or []
    loops = supervision.get("restart_patterns", {}).get("unstable_workloads") or []
    overlap = [s for s in impacted if s in loops]
    return {
        "cascade_recovery_risk": len(overlap) > 0,
        "overlapping_unstable": overlap,
        "summary": "Cascading recovery risk elevated." if overlap else "Topology recovery paths stable.",
    }
