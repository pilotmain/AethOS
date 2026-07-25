# SPDX-License-Identifier: Apache-2.0
"""Container relationships — service dependency awareness."""

from __future__ import annotations

from typing import Any


def map_container_relationships(*, runtime_snapshot: dict[str, Any], containers: list[dict[str, Any]]) -> dict[str, Any]:
    edges = runtime_snapshot.get("dependencies") or []
    if not isinstance(edges, list):
        edges = []
    if not edges and containers:
        names = [c["name"] for c in containers]
        if "api" in names:
            for dep in ("redis", "postgres", "browser-worker"):
                if dep in names:
                    edges.append({"from": "api", "to": dep, "kind": "runtime"})
    return {
        "dependency_count": len(edges),
        "edges": edges,
        "summary": f"Mapped {len(edges)} container dependency relationships.",
    }
