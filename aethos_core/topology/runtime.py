# SPDX-License-Identifier: Apache-2.0
"""Topology intelligence orchestrator."""

from __future__ import annotations

from typing import Any

from aethos_core.topology.critical_path_detection import detect_critical_paths
from aethos_core.topology.dependency_graph import build_dependency_graph
from aethos_core.topology.operational_surface_map import build_operational_surface_map
from aethos_core.topology.propagation_analysis import analyze_failure_propagation
from aethos_core.topology.service_classification import classify_services
from aethos_core.topology.topology_memory import remember_topology


def build_topology_intelligence(*, runtime_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    if not runtime_snapshot:
        from aethos_core.infrastructure.docker.runtime import _default_snapshot

        runtime_snapshot = _default_snapshot()
    graph = build_dependency_graph(runtime_snapshot=runtime_snapshot)
    classifications = classify_services(graph=graph)
    propagation = analyze_failure_propagation(
        graph=graph,
        degraded=[str(c.get("name")) for c in (runtime_snapshot.get("containers") or []) if c.get("recovery_loop")],
    )
    critical_paths = detect_critical_paths(graph=graph, classifications=classifications)
    surface = build_operational_surface_map(graph=graph, classifications=classifications)
    memory = remember_topology(graph=graph)
    return {
        "ok": True,
        "graph": graph,
        "classifications": classifications,
        "propagation": propagation,
        "critical_paths": critical_paths,
        "surface_map": surface,
        "memory": memory,
        "principle": "Infrastructure intelligence requires relationship awareness — not isolated service awareness.",
        "summary": graph.get("summary", ""),
    }
