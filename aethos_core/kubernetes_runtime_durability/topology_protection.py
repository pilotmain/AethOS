# SPDX-License-Identifier: Apache-2.0
"""Topology protection — cascading failure resistance."""

from __future__ import annotations

from typing import Any

from aethos_core.kubernetes_resilience.topology_resilience_propagation import assess_topology_resilience_propagation


def assess_topology_protection() -> dict[str, Any]:
    propagation = assess_topology_resilience_propagation()
    return {
        **propagation,
        "protected": propagation.get("resilient", False),
        "summary": "Cascading failure resistance maintained." if propagation.get("resilient") else "Topology protection monitoring active.",
    }
