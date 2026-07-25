# SPDX-License-Identifier: Apache-2.0
"""Propagation analysis — cascading failure awareness."""

from __future__ import annotations

from typing import Any


def analyze_failure_propagation(*, graph: dict[str, Any], degraded: list[str]) -> dict[str, Any]:
    edges = graph.get("edges") or []
    impacted: set[str] = set(degraded)
    changed = True
    while changed:
        changed = False
        for edge in edges:
            if not isinstance(edge, dict):
                continue
            src = str(edge.get("from") or "")
            dst = str(edge.get("to") or "")
            if src in impacted and dst not in impacted:
                impacted.add(dst)
                changed = True
    return {
        "degraded_sources": degraded,
        "potentially_impacted": sorted(impacted),
        "cascade_risk": len(impacted) > len(degraded),
        "summary": f"{len(impacted)} services potentially impacted by degradation cascade.",
    }
