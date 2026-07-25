# SPDX-License-Identifier: Apache-2.0
"""Kubernetes runtime durability aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.kubernetes_runtime_durability.mesh_recovery_resilience import assess_mesh_recovery_resilience
from aethos_core.kubernetes_runtime_durability.namespace_resilience import assess_namespace_durability
from aethos_core.kubernetes_runtime_durability.node_pressure_durability import assess_node_pressure_durability
from aethos_core.kubernetes_runtime_durability.pod_persistence import assess_pod_persistence
from aethos_core.kubernetes_runtime_durability.rollout_durability import assess_rollout_durability
from aethos_core.kubernetes_runtime_durability.topology_protection import assess_topology_protection


def assess_kubernetes_runtime_durability() -> dict[str, Any]:
    rollout = assess_rollout_durability()
    namespace = assess_namespace_durability()
    pods = assess_pod_persistence()
    pressure = assess_node_pressure_durability()
    mesh = assess_mesh_recovery_resilience()
    protection = assess_topology_protection()
    durable = rollout.get("resilient") and pods.get("resilient") and pressure.get("resilient")
    return {
        "ok": True,
        "rollout_durability": rollout,
        "namespace_resilience": namespace,
        "pod_persistence": pods,
        "node_pressure_durability": pressure,
        "mesh_recovery_resilience": mesh,
        "topology_protection": protection,
        "durable": durable,
        "summary": "Kubernetes runtime durability sustained under evolving operational conditions." if durable else "Kubernetes durability cognition active.",
    }
