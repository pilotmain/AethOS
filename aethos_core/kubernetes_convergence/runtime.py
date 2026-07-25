# SPDX-License-Identifier: Apache-2.0
"""Kubernetes convergence aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.kubernetes_convergence.namespace_stability import assess_namespace_stability
from aethos_core.kubernetes_convergence.node_pressure_cognition import assess_node_pressure
from aethos_core.kubernetes_convergence.pod_recovery_truth import assess_pod_recovery_truth
from aethos_core.kubernetes_convergence.rollout_convergence import assess_rollout_convergence
from aethos_core.kubernetes_convergence.service_mesh_recovery import assess_service_mesh_recovery
from aethos_core.kubernetes_convergence.topology_failure_propagation import assess_topology_failure_propagation


def assess_kubernetes_convergence() -> dict[str, Any]:
    rollout = assess_rollout_convergence()
    namespace = assess_namespace_stability()
    pods = assess_pod_recovery_truth()
    pressure = assess_node_pressure()
    mesh = assess_service_mesh_recovery()
    propagation = assess_topology_failure_propagation()
    converged = rollout.get("converged") and pods.get("converged") and not pressure.get("elevated")
    return {
        "ok": True,
        "rollout_convergence": rollout,
        "namespace_stability": namespace,
        "pod_recovery_truth": pods,
        "node_pressure": pressure,
        "service_mesh_recovery": mesh,
        "topology_failure_propagation": propagation,
        "converged": converged,
        "summary": "Kubernetes stability converging — topology recovery over sustained windows." if converged else "Kubernetes convergence cognition active.",
    }
