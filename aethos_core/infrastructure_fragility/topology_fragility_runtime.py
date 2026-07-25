# SPDX-License-Identifier: Apache-2.0
"""Topology fragility runtime — weak-point detection."""

from __future__ import annotations

from typing import Any

from aethos_core.infrastructure_intuition.topology_fragility import detect_topology_fragility


def assess_topology_fragility_runtime(*, fragility_score: float = 0.24) -> dict[str, Any]:
    fragility = detect_topology_fragility(fragility_score=fragility_score)
    return {
        **fragility,
        "summary": "Topology weak points identified — fragility awareness active." if fragility.get("fragile") else "No significant topology fragility currently detected.",
    }
