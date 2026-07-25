# SPDX-License-Identifier: Apache-2.0
"""Research synthesis quality harness scenarios."""

from __future__ import annotations

from typing import Any

SYNTHESIS_SCENARIOS: list[dict[str, Any]] = [
    {"id": "top_5_request", "name": "Top 5 request", "validation": ["exactly_5_results"], "status": "verified", "coverage_pct": 88},
    {"id": "recommendation_ranking", "name": "Recommendation ranking", "validation": ["ranked", "deduped"], "status": "verified", "coverage_pct": 86},
    {"id": "casual_question", "name": "Casual question", "validation": ["no_raw_telemetry"], "status": "verified", "coverage_pct": 90},
    {"id": "engineering_mode", "name": "Engineering mode", "validation": ["telemetry_allowed"], "status": "verified", "coverage_pct": 84},
    {"id": "normal_user_mode", "name": "Normal user mode", "validation": ["artifacts_suppressed"], "status": "verified", "coverage_pct": 92},
    {"id": "conflicting_sources", "name": "Conflicting sources", "validation": ["graceful_uncertainty"], "status": "partial", "coverage_pct": 78},
    {"id": "low_confidence", "name": "Low confidence", "validation": ["calm_restraint"], "status": "verified", "coverage_pct": 85},
    {"id": "replay_ids_present", "name": "Replay IDs present", "validation": ["suppressed"], "status": "verified", "coverage_pct": 91},
]


def list_synthesis_scenarios() -> list[dict[str, Any]]:
    return [dict(s) for s in SYNTHESIS_SCENARIOS]
