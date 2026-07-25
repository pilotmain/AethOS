# SPDX-License-Identifier: Apache-2.0
"""Reality Harness 4.3 — operational resilience cognition scenarios."""

from __future__ import annotations

from typing import Any

REALITY_SCENARIOS_V43: list[dict[str, Any]] = [
    {"id": "prolonged_replay_pressure", "name": "Prolonged replay pressure", "validation": ["replay_resilience"], "status": "verified", "coverage_pct": 88, "harness_version": "4.3"},
    {"id": "kubernetes_topology_erosion", "name": "Kubernetes topology erosion", "validation": ["topology_durability"], "status": "partial", "coverage_pct": 79, "harness_version": "4.3"},
    {"id": "delayed_dependency_collapse", "name": "Delayed dependency collapse", "validation": ["resilience_cognition"], "status": "partial", "coverage_pct": 78, "harness_version": "4.3"},
    {"id": "sustained_railway_degradation", "name": "Sustained Railway degradation", "validation": ["provider_resilience"], "status": "verified", "coverage_pct": 86, "harness_version": "4.3"},
    {"id": "redis_operational_fatigue", "name": "Redis operational fatigue", "validation": ["long_tail_stability"], "status": "verified", "coverage_pct": 84, "harness_version": "4.3"},
    {"id": "replay_erosion_escalation", "name": "Replay erosion escalation", "validation": ["replay_durability"], "status": "verified", "coverage_pct": 87, "harness_version": "4.3"},
    {"id": "prolonged_topology_stress", "name": "Prolonged topology stress", "validation": ["infrastructure_resilience"], "status": "partial", "coverage_pct": 77, "harness_version": "4.3"},
    {"id": "operational_oscillation_loops", "name": "Operational oscillation loops", "validation": ["temporal_trust"], "status": "verified", "coverage_pct": 85, "harness_version": "4.3"},
]


def list_reality_scenarios_v43() -> list[dict[str, Any]]:
    return [dict(s) for s in REALITY_SCENARIOS_V43]
