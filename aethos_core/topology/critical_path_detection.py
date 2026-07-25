# SPDX-License-Identifier: Apache-2.0
"""Critical path detection — operational bottlenecks."""

from __future__ import annotations

from typing import Any


def detect_critical_paths(*, graph: dict[str, Any], classifications: dict[str, Any]) -> dict[str, Any]:
    critical = classifications.get("critical") or []
    edges = graph.get("edges") or []
    bottlenecks: list[str] = []
    for svc in critical:
        downstream = sum(1 for e in edges if isinstance(e, dict) and e.get("from") == svc)
        if downstream >= 2:
            bottlenecks.append(svc)
    return {
        "critical_services": critical,
        "bottlenecks": bottlenecks,
        "summary": f"{len(bottlenecks)} critical-path bottlenecks identified." if bottlenecks else "No critical bottlenecks detected.",
    }
