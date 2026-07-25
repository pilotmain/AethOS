# SPDX-License-Identifier: Apache-2.0
"""Topology acceleration — topology instability acceleration."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_stability.topology_instability import detect_topology_instability


def detect_topology_acceleration() -> dict[str, Any]:
    instability = detect_topology_instability()
    accelerating = instability.get("unstable", False)
    return {
        **instability,
        "accelerating": accelerating,
        "summary": "Topology instability acceleration bounded." if not accelerating else "Topology weakening momentum detected.",
    }
