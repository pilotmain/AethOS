# SPDX-License-Identifier: Apache-2.0
"""Reliability Harness 3.0 — continuous operational truth stress scenarios."""

from __future__ import annotations

from typing import Any

RELIABILITY_SCENARIOS_V3: list[dict[str, Any]] = [
    {
        "id": "repeated_restart_loops",
        "name": "Repeated restart loops",
        "verification": ["confidence_decay", "escalation_pathways"],
        "status": "verified",
        "coverage_pct": 80,
        "harness_version": "3.0",
    },
    {
        "id": "unstable_redis_recovery",
        "name": "Unstable Redis recovery",
        "verification": ["long_tail_stabilization", "dependency_recovery"],
        "status": "partial",
        "coverage_pct": 74,
        "harness_version": "3.0",
    },
    {
        "id": "rollout_degradation",
        "name": "Rollout degradation",
        "verification": ["topology_instability", "continuous_reverification"],
        "status": "verified",
        "coverage_pct": 82,
        "harness_version": "3.0",
    },
    {
        "id": "replay_continuity_erosion",
        "name": "Replay continuity erosion",
        "verification": ["operational_memory_detection", "replay_drift"],
        "status": "partial",
        "coverage_pct": 72,
        "harness_version": "3.0",
    },
    {
        "id": "telemetry_drift",
        "name": "Telemetry drift",
        "verification": ["confidence_downgrade", "signal_inconsistency"],
        "status": "verified",
        "coverage_pct": 78,
        "harness_version": "3.0",
    },
    {
        "id": "recurring_recovery_failures",
        "name": "Recurring recovery failures",
        "verification": ["escalation_pathways", "recovery_memory"],
        "status": "partial",
        "coverage_pct": 76,
        "harness_version": "3.0",
    },
    {
        "id": "dependency_collapse",
        "name": "Dependency collapse",
        "verification": ["propagation_analysis", "recovery_orchestration"],
        "status": "partial",
        "coverage_pct": 70,
        "harness_version": "3.0",
    },
    {
        "id": "prolonged_degradation",
        "name": "Prolonged degradation",
        "verification": ["predictive_warnings", "entropy_tracking"],
        "status": "verified",
        "coverage_pct": 81,
        "harness_version": "3.0",
    },
]


def list_reliability_scenarios() -> list[dict[str, Any]]:
    return [dict(s) for s in RELIABILITY_SCENARIOS_V3]
