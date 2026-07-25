# SPDX-License-Identifier: Apache-2.0
"""Topology resilience propagation — cascading resilience."""

from __future__ import annotations

from typing import Any

from aethos_core.kubernetes_convergence.topology_failure_propagation import assess_topology_failure_propagation


def assess_topology_resilience_propagation() -> dict[str, Any]:
    propagation = assess_topology_failure_propagation(propagation_contained=True)
    return {
        **propagation,
        "resilient": propagation.get("propagation_contained", False),
        "summary": "Cascading resilience contained across topology." if propagation.get("propagation_contained") else "Topology resilience propagation monitoring active.",
    }
