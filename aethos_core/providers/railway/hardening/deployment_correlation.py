# SPDX-License-Identifier: Apache-2.0
"""Railway deployment correlation — logs + runtime + browser reconciliation."""

from __future__ import annotations

from typing import Any


def correlate_deployment_signals(
    *,
    deployment_truth: dict[str, Any],
    health: dict[str, Any],
    telemetry: dict[str, Any],
    browser_verified: bool = False,
) -> dict[str, Any]:
    checks = [
        deployment_truth.get("transition_detected"),
        health.get("runtime_reachable"),
        health.get("health_stabilized"),
        telemetry.get("freshness_recovered"),
    ]
    if browser_verified:
        checks.append(True)
    score = sum(1 for c in checks if c) / max(len(checks), 1)
    return {
        "correlation_score": round(score, 2),
        "aligned": score >= 0.75,
        "browser_verification": browser_verified,
        "summary": "Deployment signals correlated across runtime, health, and telemetry.",
    }
