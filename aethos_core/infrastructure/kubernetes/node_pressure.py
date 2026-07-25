# SPDX-License-Identifier: Apache-2.0
"""Node pressure — node resource intelligence."""

from __future__ import annotations

from typing import Any


def assess_node_pressure(*, runtime_snapshot: dict[str, Any]) -> dict[str, Any]:
    nodes = runtime_snapshot.get("nodes") or []
    if not isinstance(nodes, list):
        nodes = []
    pressured = [n for n in nodes if str(n.get("pressure") or "").lower() in ("elevated", "high", "critical")]
    telemetry_ok = str(runtime_snapshot.get("telemetry_status") or "normal").lower() in ("normal", "healthy", "ok")
    return {
        "pressured_nodes": pressured,
        "pressured_count": len(pressured),
        "telemetry_within_thresholds": telemetry_ok,
        "summary": (
            f"{len(pressured)} nodes report elevated pressure."
            if pressured
            else "Cluster telemetry within expected thresholds."
        ),
    }
