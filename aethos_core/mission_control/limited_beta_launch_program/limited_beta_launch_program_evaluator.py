# SPDX-License-Identifier: Apache-2.0
"""FIX 312 — limited beta launch program evaluator."""

from __future__ import annotations

from typing import Any


def derive_beta_launch_recommendation(
    *,
    overall_launch_status: str,
    at_risk_count: int,
    risk_count: int,
    healthy_count: int,
    admission_approve_count: int,
    feedback_count: int,
) -> str:
    if overall_launch_status == "BLOCKED" or risk_count >= 5:
        return "DO_NOT_LAUNCH"
    if overall_launch_status in {"READY_FOR_LIMITED_BETA", "READY_FOR_PUBLIC_LAUNCH"} and at_risk_count == 0:
        if admission_approve_count > 0 and feedback_count >= 3 and healthy_count >= 2:
            return "EXPAND_BETA"
        if overall_launch_status == "READY_FOR_PUBLIC_LAUNCH" and feedback_count >= 5:
            return "READY_FOR_PUBLIC_REVIEW"
        return "LIMITED_BETA_READY"
    if overall_launch_status == "CONDITIONAL" and at_risk_count <= 1:
        return "LIMITED_BETA_READY"
    return "DO_NOT_LAUNCH"


def aggregate_success_metrics(
    *,
    org_count: int,
    healthy_count: int,
    onboarding_ready: bool,
    provider_ready: bool,
    connected_providers: int,
    channel_ready: bool,
    audit_ready: bool,
) -> dict[str, Any]:
    activation_rate = round((healthy_count / org_count) * 100, 1) if org_count else 0.0
    onboarding_completion = 100.0 if onboarding_ready else 0.0
    provider_connection_completion = 100.0 if provider_ready and connected_providers > 0 else 0.0
    workflow_completion = 100.0 if audit_ready and channel_ready else 50.0 if audit_ready else 0.0
    customer_health_score = round(
        (
            activation_rate
            + onboarding_completion
            + provider_connection_completion
            + workflow_completion
        )
        / 4,
        1,
    )
    return {
        "activation_rate": activation_rate,
        "onboarding_completion": onboarding_completion,
        "provider_connection_completion": provider_connection_completion,
        "workflow_completion": workflow_completion,
        "customer_health_score": customer_health_score,
        "read_only": True,
    }


def classify_beta_risks(
    *,
    launch_blockers: list[str],
    support_risks: list[dict[str, Any]],
    launch_status: str,
) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = []
    if launch_status == "BLOCKED":
        risks.append(
            {
                "risk_id": "launch-blocked",
                "category": "operational",
                "level": "critical",
                "detail": "Launch assessment reports BLOCKED status",
                "read_only": True,
            }
        )
    for blocker in launch_blockers[:3]:
        risks.append(
            {
                "risk_id": f"launch-blocker-{hash(blocker) % 10000}",
                "category": "product",
                "level": "high",
                "detail": blocker,
                "read_only": True,
            }
        )
    for row in support_risks[:5]:
        risks.append(
            {
                "risk_id": row.get("risk_id") or "support-risk",
                "category": row.get("category") or "adoption",
                "level": row.get("level") or "medium",
                "detail": row.get("detail") or "Support risk from composed evidence",
                "read_only": True,
            }
        )
    if not risks:
        risks.append(
            {
                "risk_id": "beta-risk-monitoring",
                "category": "governance",
                "level": "low",
                "detail": "No critical beta risks from composed evidence — continue monitoring",
                "read_only": True,
            }
        )
    return risks
