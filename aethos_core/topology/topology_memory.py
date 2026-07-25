# SPDX-License-Identifier: Apache-2.0
"""Topology memory — persistent infrastructure understanding."""

from __future__ import annotations

from typing import Any

_TOPOLOGY_MEMORY: list[dict[str, Any]] = []


def remember_topology(*, graph: dict[str, Any], snapshot_id: str = "latest") -> dict[str, Any]:
    entry = {"snapshot_id": snapshot_id, "node_count": graph.get("node_count", 0), "edge_count": graph.get("edge_count", 0)}
    _TOPOLOGY_MEMORY.append(entry)
    if len(_TOPOLOGY_MEMORY) > 50:
        del _TOPOLOGY_MEMORY[:-50]
    return {"remembered": True, "memory_size": len(_TOPOLOGY_MEMORY), "latest": entry}


def topology_memory_state() -> dict[str, Any]:
    return {"entries": list(_TOPOLOGY_MEMORY), "count": len(_TOPOLOGY_MEMORY)}
