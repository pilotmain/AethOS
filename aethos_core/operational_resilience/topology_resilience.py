# SPDX-License-Identifier: Apache-2.0
"""Topology resilience — topology durability."""

from __future__ import annotations

from typing import Any

from aethos_core.kubernetes_resilience.topology_resilience_propagation import assess_topology_resilience_propagation


def assess_topology_durability() -> dict[str, Any]:
    topology = assess_topology_resilience_propagation()
    durable = topology.get("resilient", False)
    return {
        **topology,
        "durable": durable,
        "summary": "Topology durability signals remain healthy." if durable else "Topology durability monitoring active.",
    }
