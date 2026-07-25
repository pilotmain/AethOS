# SPDX-License-Identifier: Apache-2.0
"""FIX 310 — customer support & success foundation evaluator."""

from __future__ import annotations

from typing import Any


def score_customer_health(
    *,
    onboarding_ready: bool,
    provider_ready: bool,
    channel_ready: bool,
    billing_ready: bool,
    workspace_count: int,
    member_count: int,
    plan: str,
) -> str:
    signals = [
        onboarding_ready,
        provider_ready,
        channel_ready,
        billing_ready,
        workspace_count > 0,
        member_count > 0,
    ]
    ready_count = sum(1 for signal in signals if signal)
    if ready_count >= 5 and plan in {"pro", "enterprise", "team"}:
        return "HIGH_VALUE"
    if ready_count >= 5:
        return "HEALTHY"
    if ready_count <= 2 and member_count <= 1:
        return "NEW"
    if ready_count <= 3:
        return "AT_RISK"
    return "HEALTHY"


def classify_risks(
    *,
    org_id: str,
    org_name: str,
    health_status: str,
    onboarding_ready: bool,
    provider_ready: bool,
    billing_ready: bool,
    permission_issues: bool,
) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = []
    if health_status == "AT_RISK":
        risks.append(
            {
                "risk_id": f"low-adoption-{org_id}",
                "org_id": org_id,
                "org_name": org_name,
                "category": "low_adoption",
                "level": "high",
                "detail": "Low adoption signals across onboarding, providers, and channels",
                "read_only": True,
            }
        )
    if not onboarding_ready:
        risks.append(
            {
                "risk_id": f"onboarding-gap-{org_id}",
                "org_id": org_id,
                "org_name": org_name,
                "category": "low_adoption",
                "level": "medium",
                "detail": "Onboarding evidence incomplete",
                "read_only": True,
            }
        )
    if not provider_ready:
        risks.append(
            {
                "risk_id": f"provider-gap-{org_id}",
                "org_id": org_id,
                "org_name": org_name,
                "category": "provider_readiness_gap",
                "level": "medium",
                "detail": "Provider connection readiness gap",
                "read_only": True,
            }
        )
    if not billing_ready:
        risks.append(
            {
                "risk_id": f"billing-concern-{org_id}",
                "org_id": org_id,
                "org_name": org_name,
                "category": "billing_concern",
                "level": "medium",
                "detail": "Billing or entitlement evidence incomplete",
                "read_only": True,
            }
        )
    if permission_issues:
        risks.append(
            {
                "risk_id": f"permission-issue-{org_id}",
                "org_id": org_id,
                "org_name": org_name,
                "category": "permission_issue",
                "level": "high",
                "detail": "Permission or RBAC visibility gap detected",
                "read_only": True,
            }
        )
    return risks


def derive_opportunities(
    *,
    org_id: str,
    org_name: str,
    health_status: str,
    plan: str,
    onboarding_ready: bool,
    provider_ready: bool,
) -> list[dict[str, Any]]:
    opportunities: list[dict[str, Any]] = []
    if health_status in {"HEALTHY", "HIGH_VALUE"} and plan in {"free", "starter"}:
        opportunities.append(
            {
                "opportunity_id": f"upsell-{org_id}",
                "org_id": org_id,
                "org_name": org_name,
                "type": "upsell",
                "detail": "Healthy engagement — review plan upgrade opportunity",
                "read_only": True,
            }
        )
    if not onboarding_ready or not provider_ready:
        opportunities.append(
            {
                "opportunity_id": f"adoption-{org_id}",
                "org_id": org_id,
                "org_name": org_name,
                "type": "adoption",
                "detail": "Onboarding or provider adoption assistance may help",
                "read_only": True,
            }
        )
    if health_status in {"NEW", "AT_RISK"}:
        opportunities.append(
            {
                "opportunity_id": f"training-{org_id}",
                "org_id": org_id,
                "org_name": org_name,
                "type": "training",
                "detail": "Customer may benefit from guided onboarding or training",
                "read_only": True,
            }
        )
    return opportunities


def aggregate_support_analytics(
    *,
    health_rows: list[dict[str, Any]],
    risks: list[dict[str, Any]],
    escalations: list[dict[str, Any]],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    status_counts = {status: 0 for status in ("HEALTHY", "AT_RISK", "NEW", "HIGH_VALUE", "UNKNOWN")}
    for row in health_rows:
        status = str(row.get("health_status") or "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1

    support_notes = sum(1 for record in records if record.get("kind") == "support_note")
    success_notes = sum(1 for record in records if record.get("kind") == "customer_success_note")
    open_escalations = sum(1 for row in escalations if row.get("resolution_status") == "open")

    return {
        "customer_count": len(health_rows),
        "healthy_count": status_counts.get("HEALTHY", 0) + status_counts.get("HIGH_VALUE", 0),
        "at_risk_count": status_counts.get("AT_RISK", 0),
        "new_customer_count": status_counts.get("NEW", 0),
        "high_value_count": status_counts.get("HIGH_VALUE", 0),
        "risk_count": len(risks),
        "open_escalation_count": open_escalations,
        "support_note_count": support_notes,
        "customer_success_note_count": success_notes,
        "read_only": True,
    }
