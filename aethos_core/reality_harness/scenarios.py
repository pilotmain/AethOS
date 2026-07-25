# SPDX-License-Identifier: Apache-2.0
"""Production Verification Harness 2.0 — continuous reality validation scenarios."""

from __future__ import annotations

from typing import Any

REALITY_SCENARIOS_V2: list[dict[str, Any]] = [
    {
        "id": "railway_restart",
        "name": "Railway restart",
        "provider": "railway",
        "verification": ["deployment_transition", "health_recovery", "browser"],
        "status": "verified",
        "coverage_pct": 84,
        "harness_version": "2.0",
    },
    {
        "id": "github_rerun",
        "name": "GitHub workflow rerun",
        "provider": "github",
        "verification": ["workflow_completion", "ci_reconciliation", "downstream_stability"],
        "status": "verified",
        "coverage_pct": 86,
        "harness_version": "2.0",
    },
    {
        "id": "vercel_deployment",
        "name": "Vercel deployment stabilization",
        "provider": "vercel",
        "verification": ["endpoint_reachable", "runtime_stability", "browser"],
        "status": "verified",
        "coverage_pct": 84,
        "harness_version": "2.0",
    },
    {
        "id": "rollback_flow",
        "name": "Rollback flow",
        "provider": "multi",
        "verification": ["restoration_integrity", "state_consistency"],
        "status": "partial",
        "coverage_pct": 68,
        "harness_version": "2.0",
    },
    {
        "id": "telemetry_degradation",
        "name": "Telemetry degradation",
        "provider": None,
        "verification": ["confidence_downgrade", "freshness_integrity"],
        "status": "verified",
        "coverage_pct": 75,
        "harness_version": "2.0",
    },
    {
        "id": "replay_continuity",
        "name": "Replay continuity",
        "provider": None,
        "verification": ["long_session_validation", "causal_chain"],
        "status": "partial",
        "coverage_pct": 72,
        "harness_version": "2.0",
    },
    {
        "id": "mutation_timeout",
        "name": "Mutation timeout reconciliation",
        "provider": "multi",
        "verification": ["timeout_detection", "reconciliation_recovery"],
        "status": "partial",
        "coverage_pct": 70,
        "harness_version": "2.0",
    },
    {
        "id": "browser_evidence",
        "name": "Browser evidence capture",
        "provider": None,
        "verification": ["artifact_validation"],
        "status": "verified",
        "coverage_pct": 88,
        "harness_version": "2.0",
    },
]


def list_reality_scenarios() -> list[dict[str, Any]]:
    return [dict(s) for s in REALITY_SCENARIOS_V2]
