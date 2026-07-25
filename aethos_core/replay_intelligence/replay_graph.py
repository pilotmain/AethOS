# SPDX-License-Identifier: Apache-2.0
"""Replay graph — causal replay graph construction."""

from __future__ import annotations

from typing import Any
from uuid import uuid4


def build_replay_graph(*, events: list[dict[str, Any]], chains: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Build causal replay graph from events and inferred chains."""
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for i, event in enumerate(events[:20]):
        nid = f"node-{i}"
        nodes.append(
            {
                "id": nid,
                "label": str(event.get("summary") or event.get("detail") or event.get("source"))[:80],
                "source": event.get("source") or event.get("category"),
                "at": event.get("at"),
            }
        )
        if i > 0:
            edges.append({"from": f"node-{i-1}", "to": nid, "kind": "temporal"})

    for chain in chains or []:
        steps = chain.get("steps") or []
        prev = None
        for j, step in enumerate(steps):
            nid = f"chain-{chain.get('chain_id', 'x')}-{j}"
            nodes.append({"id": nid, "label": step, "source": "causal", "at": None})
            if prev:
                edges.append({"from": prev, "to": nid, "kind": "causal"})
            prev = nid

    return {
        "graph_id": f"rgraph-{uuid4().hex[:10]}",
        "nodes": nodes[:30],
        "edges": edges[:40],
        "node_count": len(nodes),
        "edge_count": len(edges),
    }
