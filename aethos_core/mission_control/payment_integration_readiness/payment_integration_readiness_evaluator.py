# SPDX-License-Identifier: Apache-2.0
"""FIX 308 — payment integration readiness evaluator."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_evaluator import (
    normalize_commercial_plan,
    plan_limits,
    upgrade_opportunities,
    usage_within_limits,
)
from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_contract import (
    BILLING_EVENT_TYPES,
    PAYMENT_PROVIDERS,
    SUBSCRIPTION_LIFECYCLE_STATES,
    USAGE_MONETIZATION_CATEGORIES,
)


def resolve_subscription_lifecycle_state(*, commercial_plan: str, trial_status: str) -> str:
    if commercial_plan == "FREE" and trial_status == "eligible":
        return "trial"
    if commercial_plan == "FREE":
        return "active"
    return "active"


def payment_provider_readiness_rows() -> list[dict[str, Any]]:
    rows = []
    for provider in PAYMENT_PROVIDERS:
        rows.append(
            {
                "provider": provider,
                "integration_status": "readiness_only",
                "configured": False,
                "api_mutation_enabled": False,
                "payment_processing_enabled": False,
                "credit_card_storage_enabled": False,
                "readiness_model": "future_integration",
                "read_only": True,
            }
        )
    return rows


def subscription_lifecycle_rows(*, commercial_plan: str, trial_status: str) -> list[dict[str, Any]]:
    current = resolve_subscription_lifecycle_state(
        commercial_plan=commercial_plan,
        trial_status=trial_status,
    )
    rows = []
    for state in SUBSCRIPTION_LIFECYCLE_STATES:
        rows.append(
            {
                "state": state,
                "supported_in_model": True,
                "current_for_tenant": state == current,
                "subscription_mutation_authority": False,
                "read_only": True,
            }
        )
    return rows


def billing_event_model_rows(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for event_type in BILLING_EVENT_TYPES:
        matching = [r for r in records if event_type.replace("_", " ") in str(r.get("content") or "").lower()]
        rows.append(
            {
                "event_type": event_type,
                "modeled": True,
                "processed": False,
                "record_count": len(matching),
                "payment_processing_enabled": False,
                "read_only": True,
            }
        )
    return rows


def usage_monetization_rows(*, plan: str, usage: dict[str, int]) -> list[dict[str, Any]]:
    limits = plan_limits(plan)
    consumption = usage_within_limits(plan=plan, usage=usage)
    limit_map = {row["metric"]: row for row in consumption.get("limits") or []}
    rows = []
    for category, metric in USAGE_MONETIZATION_CATEGORIES:
        row = limit_map.get(metric, {})
        rows.append(
            {
                "category": category,
                "metric": metric,
                "current_usage": row.get("current", usage.get(metric.replace("_count", ""), 0)),
                "plan_limit": row.get("maximum"),
                "future_billable": True,
                "entitlement_consumption": row.get("within_limit", True),
                "read_only": True,
            }
        )
    return rows


def commercial_analytics(*, commercial_plan: str, org_count: int) -> dict[str, Any]:
    return {
        "tenant_distribution": {"current_org_count": org_count},
        "plan_distribution": {commercial_plan: 1},
        "trial_adoption": commercial_plan == "FREE",
        "upgrade_opportunities": upgrade_opportunities(plan=commercial_plan),
        "read_only": True,
    }


def commercial_governance_gaps(
    *,
    commercial_plan: str,
    usage: dict[str, int],
    billing_identity_complete: bool,
) -> list[dict[str, Any]]:
    gaps = []
    if not billing_identity_complete:
        gaps.append({"gap": "missing_billing_identity_reference", "severity": "medium"})
    if usage.get("executions", 0) == 0:
        gaps.append({"gap": "missing_execution_usage_signal", "severity": "low"})
    if commercial_plan == "FREE":
        gaps.append({"gap": "no_paid_subscription_reference", "severity": "informational"})
    return gaps
