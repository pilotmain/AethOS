# SPDX-License-Identifier: Apache-2.0
"""Topology stability — dependency-aware trust."""

from __future__ import annotations

from typing import Any


def score_topology_stability(*, drift: dict[str, Any]) -> dict[str, Any]:
    stable = not drift.get("topology_instability", {}).get("topology_volatile", True)
    bounded = drift.get("drift_bounded", False)
    score = 0.82 if stable and bounded else 0.58 if bounded else 0.4
    return {
        "topology_stability_score": round(score, 2),
        "summary": "Topology stability supports production confidence." if score >= 0.7 else "Topology stability under observation.",
    }
