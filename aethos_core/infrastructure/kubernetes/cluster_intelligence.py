# SPDX-License-Identifier: Apache-2.0
"""Cluster intelligence — cluster topology awareness."""

from __future__ import annotations

from typing import Any


def assess_cluster_topology(*, runtime_snapshot: dict[str, Any]) -> dict[str, Any]:
    nodes = runtime_snapshot.get("nodes") or []
    namespaces = runtime_snapshot.get("namespaces") or []
    if not isinstance(nodes, list):
        nodes = []
    if not isinstance(namespaces, list):
        namespaces = []
    return {
        "node_count": len(nodes),
        "namespace_count": len(namespaces),
        "nodes": nodes,
        "namespaces": namespaces,
        "summary": f"Cluster spans {len(nodes)} nodes across {len(namespaces)} namespaces.",
    }
