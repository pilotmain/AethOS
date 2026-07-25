# SPDX-License-Identifier: Apache-2.0
"""Topology pressure — cascading instability."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_stabilization.topology_decay import analyze_topology_decay


def assess_topology_pressure() -> dict[str, Any]:
    decay = analyze_topology_decay()
    return {
        **decay,
        "pressure_elevated": not decay.get("cascade_bounded", True),
        "summary": "Cascading instability pressure elevated." if not decay.get("cascade_bounded") else "Topology pressure bounded.",
    }
