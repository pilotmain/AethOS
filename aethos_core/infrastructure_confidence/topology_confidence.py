# SPDX-License-Identifier: Apache-2.0
"""Topology confidence — relationship-aware scoring."""

from __future__ import annotations

from typing import Any


def score_topology_confidence(*, topology: dict[str, Any]) -> dict[str, Any]:
    graph = topology.get("graph") or {}
    propagation = topology.get("propagation") or {}
    node_score = min(1.0, (graph.get("node_count") or 0) / 5)
    cascade_penalty = 0.15 if propagation.get("cascade_risk") else 0.0
    score = max(0.0, min(1.0, node_score - cascade_penalty + 0.5))
    return {"topology_confidence": round(score, 2), "cascade_risk": propagation.get("cascade_risk", False)}
