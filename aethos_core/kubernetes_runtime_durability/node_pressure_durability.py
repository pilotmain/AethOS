# SPDX-License-Identifier: Apache-2.0
"""Node pressure durability — cluster resilience."""

from __future__ import annotations

from typing import Any

from aethos_core.kubernetes_resilience.node_pressure_resilience import assess_node_pressure_resilience


def assess_node_pressure_durability() -> dict[str, Any]:
    return assess_node_pressure_resilience()
