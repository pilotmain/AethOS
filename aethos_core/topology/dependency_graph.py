# SPDX-License-Identifier: Apache-2.0
"""Dependency graph — runtime relationships."""

from __future__ import annotations

from typing import Any


def build_dependency_graph(*, runtime_snapshot: dict[str, Any]) -> dict[str, Any]:
    edges = runtime_snapshot.get("dependencies") or runtime_snapshot.get("service_routes") or []
    if not isinstance(edges, list):
        edges = []
    nodes: dict[str, dict[str, Any]] = {}
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        for key in ("from", "to"):
            name = str(edge.get(key) or "")
            if name and name not in nodes:
                nodes[name] = {"id": name, "kind": "service"}
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": list(nodes.values()),
        "edges": edges,
        "summary": f"Topology graph: {len(nodes)} services, {len(edges)} relationships.",
    }
