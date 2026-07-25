# SPDX-License-Identifier: Apache-2.0
"""Reality Harness 4.1 — sustained runtime erosion scenarios."""

from __future__ import annotations

from typing import Any

REALITY_SCENARIOS_V41: list[dict[str, Any]] = [
    {"id": "railway_delayed_degradation", "name": "Railway delayed degradation", "validation": ["runtime_patience"], "status": "verified", "coverage_pct": 87, "harness_version": "4.1"},
    {"id": "kubernetes_rollout_erosion", "name": "Kubernetes rollout erosion", "validation": ["topology_convergence"], "status": "partial", "coverage_pct": 79, "harness_version": "4.1"},
    {"id": "redis_pressure_instability", "name": "Redis pressure instability", "validation": ["sustained_recovery"], "status": "partial", "coverage_pct": 75, "harness_version": "4.1"},
    {"id": "replay_continuity_drift", "name": "Replay continuity drift", "validation": ["replay_truth"], "status": "partial", "coverage_pct": 73, "harness_version": "4.1"},
    {"id": "rollback_delayed_decay", "name": "Rollback delayed decay", "validation": ["rollback_integrity"], "status": "verified", "coverage_pct": 82, "harness_version": "4.1"},
    {"id": "prolonged_recovery", "name": "Prolonged recovery", "validation": ["operational_patience"], "status": "verified", "coverage_pct": 84, "harness_version": "4.1"},
    {"id": "dependency_collapse", "name": "Dependency collapse", "validation": ["topology_stabilization"], "status": "partial", "coverage_pct": 76, "harness_version": "4.1"},
    {"id": "ci_instability_drift", "name": "CI instability drift", "validation": ["execution_reconciliation"], "status": "verified", "coverage_pct": 86, "harness_version": "4.1"},
]


def list_reality_scenarios_v41() -> list[dict[str, Any]]:
    return [dict(s) for s in REALITY_SCENARIOS_V41]
