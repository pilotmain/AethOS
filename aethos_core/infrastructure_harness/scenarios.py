# SPDX-License-Identifier: Apache-2.0
"""Infrastructure Reality Harness — continuous infrastructure validation scenarios."""

from __future__ import annotations

from typing import Any

INFRASTRUCTURE_SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "pod_restart",
        "name": "Pod restart",
        "substrate": "kubernetes",
        "verification": ["readiness", "stabilization"],
        "status": "verified",
        "coverage_pct": 82,
        "harness_version": "1.0",
    },
    {
        "id": "container_crash_recovery",
        "name": "Container crash recovery",
        "substrate": "docker",
        "verification": ["runtime_reconciliation", "health_recovery"],
        "status": "verified",
        "coverage_pct": 80,
        "harness_version": "1.0",
    },
    {
        "id": "deployment_rollout",
        "name": "Deployment rollout",
        "substrate": "kubernetes",
        "verification": ["topology_stabilization", "service_routing"],
        "status": "verified",
        "coverage_pct": 84,
        "harness_version": "1.0",
    },
    {
        "id": "redis_pressure",
        "name": "Redis pressure",
        "substrate": "docker",
        "verification": ["recovery_verification", "dependency_integrity"],
        "status": "partial",
        "coverage_pct": 72,
        "harness_version": "1.0",
    },
    {
        "id": "postgres_recovery",
        "name": "PostgreSQL recovery",
        "substrate": "docker",
        "verification": ["dependency_integrity", "data_runtime"],
        "status": "partial",
        "coverage_pct": 74,
        "harness_version": "1.0",
    },
    {
        "id": "cluster_degradation",
        "name": "Cluster degradation",
        "substrate": "kubernetes",
        "verification": ["confidence_downgrade", "node_pressure"],
        "status": "partial",
        "coverage_pct": 70,
        "harness_version": "1.0",
    },
    {
        "id": "restart_loops",
        "name": "Restart loops",
        "substrate": "multi",
        "verification": ["anomaly_escalation", "supervision_memory"],
        "status": "verified",
        "coverage_pct": 78,
        "harness_version": "1.0",
    },
    {
        "id": "namespace_drift",
        "name": "Namespace drift",
        "substrate": "kubernetes",
        "verification": ["reconciliation_alerts", "drift_detection"],
        "status": "partial",
        "coverage_pct": 68,
        "harness_version": "1.0",
    },
]


def list_infrastructure_scenarios() -> list[dict[str, Any]]:
    return [dict(s) for s in INFRASTRUCTURE_SCENARIOS]
