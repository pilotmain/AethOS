# SPDX-License-Identifier: Apache-2.0
"""Kubernetes resilience aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.kubernetes_resilience.mesh_resilience import assess_mesh_resilience
from aethos_core.kubernetes_resilience.namespace_resilience import assess_namespace_resilience
from aethos_core.kubernetes_resilience.node_pressure_resilience import assess_node_pressure_resilience
from aethos_core.kubernetes_resilience.pod_recovery_resilience import assess_pod_recovery_resilience
from aethos_core.kubernetes_resilience.rollout_resilience import assess_rollout_resilience
from aethos_core.kubernetes_resilience.topology_resilience_propagation import assess_topology_resilience_propagation


def assess_kubernetes_resilience() -> dict[str, Any]:
    rollout = assess_rollout_resilience()
    namespace = assess_namespace_resilience()
    pods = assess_pod_recovery_resilience()
    pressure = assess_node_pressure_resilience()
    mesh = assess_mesh_resilience()
    propagation = assess_topology_resilience_propagation()
    resilient = rollout.get("resilient") and pods.get("resilient") and pressure.get("resilient")
    return {
        "ok": True,
        "rollout_resilience": rollout,
        "namespace_resilience": namespace,
        "pod_recovery_resilience": pods,
        "node_pressure_resilience": pressure,
        "mesh_resilience": mesh,
        "topology_resilience_propagation": propagation,
        "resilient": resilient,
        "summary": "Kubernetes resilience durable — sustained topology stability under operational pressure." if resilient else "Kubernetes resilience cognition active.",
    }
