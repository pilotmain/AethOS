# SPDX-License-Identifier: Apache-2.0
"""FIX 315 — launch decision package evaluator."""

from __future__ import annotations

from typing import Any


def derive_launch_recommendation_package(
    *,
    freeze_recommendation: str,
    ops_recommendation: str,
    beta_recommendation: str,
    blocker_count: int,
    critical_risk_count: int,
    platform_healthy: bool,
) -> str:
    if blocker_count > 0 or critical_risk_count > 0 or freeze_recommendation == "NOT_READY":
        return "DO_NOT_PROCEED"
    if freeze_recommendation == "READY_FOR_LAUNCH_DECISION" and platform_healthy:
        return "READY_FOR_LAUNCH_DECISION"
    if freeze_recommendation == "PUBLIC_REVIEW_READY" or ops_recommendation == "PREPARE_PUBLIC_REVIEW":
        return "PUBLIC_REVIEW_READY"
    if ops_recommendation in {"EXPAND_BETA", "CONTINUE_BETA"}:
        return "EXPAND_BETA"
    if freeze_recommendation == "LIMITED_BETA_READY":
        return "LIMITED_BETA_ONLY"
    if beta_recommendation in {"READY_FOR_LIMITED_BETA", "CONTINUE_BETA"}:
        return "LIMITED_BETA_ONLY"
    return "DO_NOT_PROCEED"


def bucket_risks_by_level(risks: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": [],
    }
    for row in risks:
        level = str(row.get("level") or "medium").lower()
        if level not in buckets:
            level = "medium"
        buckets[level].append(row)
    return buckets


def categorize_blockers(
    *,
    blockers: list[dict[str, Any]],
    overall_launch_status: str,
) -> dict[str, list[dict[str, Any]]]:
    open_blockers = list(blockers)
    conditional_blockers = (
        open_blockers
        if overall_launch_status in {"CONDITIONAL", "READY_FOR_LIMITED_BETA"}
        else []
    )
    return {
        "open": open_blockers,
        "resolved": [],
        "conditional": conditional_blockers,
    }


def categorize_capabilities(
    capabilities: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    proven: list[dict[str, Any]] = []
    operational: list[dict[str, Any]] = []
    experimental: list[dict[str, Any]] = []
    planned: list[dict[str, Any]] = []

    for cap in capabilities:
        status = str(cap.get("status") or "").upper()
        if status in {"PROVEN", "CONDITIONALLY_TRUSTED"}:
            proven.append(cap)
        elif status == "OPERATIONAL":
            operational.append(cap)
        elif status == "EXPERIMENTAL":
            experimental.append(cap)
        elif status in {"PLANNED", "BLOCKED", "DEPRECATED"}:
            planned.append(cap)
        else:
            experimental.append(cap)

    return {
        "proven": proven,
        "operational": operational,
        "experimental": experimental,
        "planned": planned,
    }
