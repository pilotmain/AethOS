# SPDX-License-Identifier: Apache-2.0
"""Topology instability — dependency collapse."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_operational_decay.topology_erosion import assess_topology_erosion


def detect_topology_instability() -> dict[str, Any]:
    erosion = assess_topology_erosion()
    unstable = erosion.get("pressure_elevated", False)
    return {
        **erosion,
        "unstable": unstable,
        "summary": "Topology instability detected." if unstable else "Topology stability held over extended runtime periods.",
    }
