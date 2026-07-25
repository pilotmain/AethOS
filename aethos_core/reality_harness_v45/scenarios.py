# SPDX-License-Identifier: Apache-2.0
"""Reality Harness 4.5 — long-tail survivability stress scenarios."""

from __future__ import annotations

from typing import Any

REALITY_SCENARIOS_V45: list[dict[str, Any]] = [
    {"id": "prolonged_replay_survivability_erosion", "name": "Prolonged replay survivability erosion", "validation": ["replay_longevity"], "status": "verified", "coverage_pct": 90, "harness_version": "4.5"},
    {"id": "delayed_topology_sustainability_collapse", "name": "Delayed topology sustainability collapse", "validation": ["topology_survivability"], "status": "verified", "coverage_pct": 89, "harness_version": "4.5"},
    {"id": "prolonged_railway_endurance_degradation", "name": "Prolonged Railway endurance degradation", "validation": ["provider_survivability"], "status": "verified", "coverage_pct": 88, "harness_version": "4.5"},
    {"id": "operational_exhaustion_accumulation", "name": "Operational exhaustion accumulation", "validation": ["resilience_exhaustion"], "status": "verified", "coverage_pct": 91, "harness_version": "4.5"},
    {"id": "cascading_dependency_endurance_decay", "name": "Cascading dependency endurance decay", "validation": ["topology_sustainability"], "status": "verified", "coverage_pct": 89, "harness_version": "4.5"},
    {"id": "replay_persistence_fatigue", "name": "Replay persistence fatigue", "validation": ["replay_continuity"], "status": "verified", "coverage_pct": 90, "harness_version": "4.5"},
    {"id": "prolonged_stabilization_strain", "name": "Prolonged stabilization strain", "validation": ["endurance_cognition"], "status": "verified", "coverage_pct": 87, "harness_version": "4.5"},
    {"id": "long_tail_survivability_erosion", "name": "Long-tail survivability erosion", "validation": ["forecasting_cognition"], "status": "verified", "coverage_pct": 92, "harness_version": "4.5"},
]


def list_reality_scenarios_v45() -> list[dict[str, Any]]:
    return [dict(s) for s in REALITY_SCENARIOS_V45]
