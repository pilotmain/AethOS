# SPDX-License-Identifier: Apache-2.0
"""Topology instability — dependency volatility."""

from __future__ import annotations

from typing import Any


def assess_topology_instability(*, topology: dict[str, Any]) -> dict[str, Any]:
    propagation = topology.get("propagation") or {}
    cascade = propagation.get("cascade_risk", False)
    critical = topology.get("critical_paths", {}).get("bottlenecks") or []
    volatile = cascade or len(critical) >= 2
    return {
        "topology_volatile": volatile,
        "cascade_risk": cascade,
        "bottleneck_count": len(critical),
        "summary": "Topology stability maintained." if not volatile else "Dependency volatility detected.",
    }
