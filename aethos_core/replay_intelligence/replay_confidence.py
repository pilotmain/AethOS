# SPDX-License-Identifier: Apache-2.0
"""Replay confidence — replay integrity scoring."""

from __future__ import annotations

from typing import Any

from aethos_core.reliability.replay_integrity import assess_replay_integrity


def score_replay_confidence(
    *,
    replays: list[dict[str, Any]] | None = None,
    graph: dict[str, Any] | None = None,
    chains: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Score confidence in replay reconstruction."""
    integrity = assess_replay_integrity(replays=replays)
    chain_conf = 0.0
    if chains:
        chain_conf = sum(float(c.get("confidence") or 0.5) for c in chains) / len(chains)
    graph_nodes = int((graph or {}).get("node_count") or 0)
    coverage = min(1.0, graph_nodes / 8)

    raw = 0.35 + coverage * 0.25 + chain_conf * 0.3
    if integrity.get("integrity") == "healthy":
        raw += 0.15
    elif integrity.get("integrity") in ("missing", "incomplete"):
        raw -= 0.2

    return {
        "replay_confidence": round(max(0.25, min(raw, 0.92)), 2),
        "integrity": integrity,
        "chain_count": len(chains or []),
        "graph_coverage": round(coverage, 2),
    }
