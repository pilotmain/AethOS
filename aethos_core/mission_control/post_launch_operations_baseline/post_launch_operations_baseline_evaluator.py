# SPDX-License-Identifier: Apache-2.0
"""FIX 316 — post-launch operations baseline evaluator."""

from __future__ import annotations

from typing import Any


def assess_platform_health(
    *,
    monitoring_ok: bool,
    monitoring_classification: str,
    platform_healthy: bool,
    deployment_health: bool,
) -> str:
    if not monitoring_ok:
        return "UNKNOWN"
    if monitoring_classification in {"INCIDENT", "DEGRADED"} or not platform_healthy:
        return "DEGRADED"
    if monitoring_classification == "WARNING" or not deployment_health:
        return "ATTENTION"
    return "HEALTHY"


def assess_customer_health(
    *,
    healthy_count: int,
    at_risk_count: int,
    beta_participants: int,
    support_ready: bool,
) -> str:
    if not support_ready:
        return "UNKNOWN"
    if at_risk_count > healthy_count:
        return "AT_RISK"
    if at_risk_count > 0:
        return "ATTENTION"
    if healthy_count > 0 or beta_participants > 0:
        return "HEALTHY"
    return "EARLY"


def categorize_capabilities_for_baseline(
    capabilities: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    proven: list[dict[str, Any]] = []
    experimental: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []

    for cap in capabilities:
        status = str(cap.get("status") or "").upper()
        if status in {"PROVEN", "OPERATIONAL", "CONDITIONALLY_TRUSTED"}:
            proven.append(cap)
        elif status in {"BLOCKED", "DEPRECATED"}:
            blocked.append(cap)
        else:
            experimental.append(cap)

    return {"proven": proven, "experimental": experimental, "blocked": blocked}


def summarize_trust_progression(
    *,
    trust_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    available = [row for row in trust_rows if row.get("available")]
    regressions = [
        row
        for row in available
        if str(row.get("trust_state") or "").upper() in {"HOLD", "BLOCK", "REJECT"}
    ]
    progressions = [
        row
        for row in available
        if str(row.get("trust_state") or "").upper() in {"APPROVE", "EXPAND", "CONTINUE"}
    ]
    return {
        "trust_status_count": len(available),
        "trust_progressions": progressions,
        "trust_regressions": regressions,
        "trust_stable": len(regressions) == 0,
    }
