# SPDX-License-Identifier: Apache-2.0
"""Reality Harness 4.0 — production execution realism scenarios."""

from __future__ import annotations

from typing import Any

REALITY_SCENARIOS_V4: list[dict[str, Any]] = [
    {"id": "railway_restart_loop", "name": "Railway restart loop", "validation": ["sustained_convergence"], "status": "verified", "coverage_pct": 86, "harness_version": "4.0"},
    {"id": "kubernetes_rollout_erosion", "name": "Kubernetes rollout erosion", "validation": ["topology_recovery"], "status": "partial", "coverage_pct": 78, "harness_version": "4.0"},
    {"id": "redis_pressure_collapse", "name": "Redis pressure collapse", "validation": ["downstream_stabilization"], "status": "partial", "coverage_pct": 74, "harness_version": "4.0"},
    {"id": "replay_degradation", "name": "Replay degradation", "validation": ["confidence_decay"], "status": "partial", "coverage_pct": 72, "harness_version": "4.0"},
    {"id": "rollback_partial_recovery", "name": "Rollback partial recovery", "validation": ["dependency_truth"], "status": "partial", "coverage_pct": 76, "harness_version": "4.0"},
    {"id": "telemetry_drift", "name": "Telemetry drift", "validation": ["operational_reconciliation"], "status": "verified", "coverage_pct": 80, "harness_version": "4.0"},
    {"id": "prolonged_degradation", "name": "Prolonged degradation", "validation": ["runtime_patience"], "status": "verified", "coverage_pct": 83, "harness_version": "4.0"},
    {"id": "ci_rerun_mismatch", "name": "CI rerun mismatch", "validation": ["execution_truth"], "status": "verified", "coverage_pct": 87, "harness_version": "4.0"},
]


def list_reality_scenarios_v4() -> list[dict[str, Any]]:
    return [dict(s) for s in REALITY_SCENARIOS_V4]
