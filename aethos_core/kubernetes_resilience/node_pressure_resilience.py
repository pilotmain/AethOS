# SPDX-License-Identifier: Apache-2.0
"""Node pressure resilience — cluster pressure durability."""

from __future__ import annotations

from typing import Any

from aethos_core.kubernetes_convergence.node_pressure_cognition import assess_node_pressure


def assess_node_pressure_resilience() -> dict[str, Any]:
    pressure = assess_node_pressure(pressure_score=0.30)
    resilient = not pressure.get("elevated", False)
    return {
        **pressure,
        "resilient": resilient,
        "summary": "Node pressure resilience held." if resilient else "Node pressure resilience monitoring active.",
    }
