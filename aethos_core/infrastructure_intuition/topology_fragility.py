# SPDX-License-Identifier: Apache-2.0
"""Topology fragility — weak-point detection."""

from __future__ import annotations

from typing import Any


def detect_topology_fragility(*, fragility_score: float = 0.28) -> dict[str, Any]:
    fragile = fragility_score > 0.6
    return {
        "fragility_score": fragility_score,
        "fragile": fragile,
        "summary": "Topology fragility detected — weak points identified." if fragile else "No significant topology fragility currently detected.",
    }
