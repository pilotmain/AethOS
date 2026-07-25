# SPDX-License-Identifier: Apache-2.0
"""Reality Harness 4.2 — recovery continuity cognition scenarios."""

from __future__ import annotations

from typing import Any

REALITY_SCENARIOS_V42: list[dict[str, Any]] = [
    {"id": "delayed_replay_erosion", "name": "Delayed replay erosion", "validation": ["replay_persistence"], "status": "verified", "coverage_pct": 87, "harness_version": "4.2"},
    {"id": "kubernetes_recovery_oscillation", "name": "Kubernetes recovery oscillation", "validation": ["topology_continuity"], "status": "partial", "coverage_pct": 79, "harness_version": "4.2"},
    {"id": "redis_prolonged_pressure", "name": "Redis prolonged pressure", "validation": ["stability_intelligence"], "status": "partial", "coverage_pct": 78, "harness_version": "4.2"},
    {"id": "railway_delayed_instability", "name": "Railway delayed instability", "validation": ["recovery_continuity"], "status": "verified", "coverage_pct": 85, "harness_version": "4.2"},
    {"id": "dependency_convergence_collapse", "name": "Dependency convergence collapse", "validation": ["downstream_trust"], "status": "partial", "coverage_pct": 77, "harness_version": "4.2"},
    {"id": "topology_degradation", "name": "Topology degradation", "validation": ["convergence_cognition"], "status": "verified", "coverage_pct": 84, "harness_version": "4.2"},
    {"id": "prolonged_verification_decay", "name": "Prolonged verification decay", "validation": ["temporal_trust"], "status": "verified", "coverage_pct": 83, "harness_version": "4.2"},
    {"id": "operational_fragility_regression", "name": "Operational fragility regression", "validation": ["long_tail_resilience"], "status": "verified", "coverage_pct": 86, "harness_version": "4.2"},
]


def list_reality_scenarios_v42() -> list[dict[str, Any]]:
    return [dict(s) for s in REALITY_SCENARIOS_V42]
