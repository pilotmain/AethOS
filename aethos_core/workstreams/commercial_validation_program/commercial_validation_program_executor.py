# SPDX-License-Identifier: Apache-2.0
"""FIX 351 / WORKSTREAM_F5 — commercial validation executor."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_evaluator import (
    normalize_commercial_plan,
    plan_limits,
    upgrade_opportunities,
    usage_within_limits,
)
from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_evaluator import (
    commercial_analytics,
    commercial_governance_gaps,
)
from aethos_core.workstreams.commercial_validation_program.commercial_validation_program_contract import (
    COMMERCIAL_COHORT_MIN_SIZE,
    COMMERCIAL_PLANS,
)
from aethos_core.workstreams.commercial_validation_program.commercial_validation_program_store import (
    list_commercial_cohort_registry_entries,
    register_commercial_cohort_customer,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_executor import (
    build_customer_adoption_report,
    compute_validation_metrics,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_store import (
    list_customer_pilot_run_registry_entries,
)


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in re.finditer(r"(\w+)\s*=\s*([^,]+?)(?=,\s*\w+\s*=|$)", blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def _cohort_entries(*, program_session_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in list_commercial_cohort_registry_entries()
        if str(row.get("program_session_id") or program_session_id) == program_session_id
    ]


def _customer_runs(customer_session_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in list_customer_pilot_run_registry_entries()
        if str(row.get("session_id") or "") == customer_session_id
    ]


def _normalize_plan(plan: str | None) -> str:
    raw = str(plan or "FREE").strip().upper()
    if raw in COMMERCIAL_PLANS:
        return raw
    return normalize_commercial_plan(raw.lower())


def _customer_metrics(customer_session_id: str) -> dict[str, Any]:
    if not customer_session_id:
        return {}
    adoption = build_customer_adoption_report(session_id=customer_session_id)
    metrics = compute_validation_metrics(session_id=customer_session_id)
    return {
        **metrics,
        "activation_rate": 1.0 if adoption.get("first_use") else 0.0,
        "onboarding_complete": adoption.get("first_use") is True,
    }


def build_commercial_cohort_registry(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    segments = sorted({str(c.get("segment") or "general") for c in cohort})
    plans = sorted({_normalize_plan(str(c.get("plan") or "FREE")) for c in cohort})
    return {
        "registry_id": "commercial-cohort-registry",
        "program_session_id": program_session_id,
        "cohort_size": len(cohort),
        "minimum_cohort_size": COMMERCIAL_COHORT_MIN_SIZE,
        "customers": cohort,
        "segments": segments,
        "plans_in_use": plans,
        "read_only": True,
    }


def build_adoption_to_plan_report(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    by_plan: dict[str, dict[str, Any]] = {}
    for customer in cohort:
        plan = _normalize_plan(str(customer.get("plan") or "FREE"))
        customer_sid = str(customer.get("customer_session_id") or "")
        metrics = _customer_metrics(customer_sid)
        bucket = by_plan.setdefault(
            plan,
            {
                "plan": plan,
                "customer_count": 0,
                "activation_count": 0,
                "onboarding_complete_count": 0,
                "adoption_total": 0.0,
            },
        )
        bucket["customer_count"] += 1
        bucket["activation_count"] += 1 if metrics.get("activation_rate", 0) >= 1.0 else 0
        bucket["onboarding_complete_count"] += 1 if metrics.get("onboarding_complete") else 0
        bucket["adoption_total"] += float(metrics.get("adoption_rate") or 0.0)

    plan_rows = []
    for plan, bucket in by_plan.items():
        count = bucket["customer_count"] or 1
        plan_rows.append(
            {
                "plan": plan,
                "customer_count": bucket["customer_count"],
                "activation_rate": round(bucket["activation_count"] / count, 3),
                "onboarding_completion_rate": round(bucket["onboarding_complete_count"] / count, 3),
                "adoption_rate": round(bucket["adoption_total"] / count, 3),
                "fix_305_entitlements_reference": {"module": "FIX 305", "plan": plan, "read_only": True},
                "fix_308_payment_readiness_reference": {"module": "FIX 308", "plan": plan, "read_only": True},
                "fix_318_product_analytics_reference": {"module": "FIX 318", "plan": plan, "read_only": True},
                "fix_320_growth_adoption_reference": {"module": "FIX 320", "plan": plan, "read_only": True},
            }
        )

    return {
        "report_id": "adoption-to-plan-report",
        "program_session_id": program_session_id,
        "plans": plan_rows,
        "plan_attractiveness_demonstrated": any(row.get("adoption_rate", 0) >= 0.5 for row in plan_rows),
        "composed_from_fix_305_308_318_320": True,
        "payment_processing_performed": False,
        "read_only": True,
    }


def build_commercial_retention_report(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    by_plan: dict[str, list[dict[str, Any]]] = {}
    for customer in cohort:
        plan = _normalize_plan(str(customer.get("plan") or "FREE"))
        customer_sid = str(customer.get("customer_session_id") or "")
        by_plan.setdefault(plan, []).append(_customer_metrics(customer_sid))

    plan_rows = []
    churn_indicators: list[dict[str, Any]] = []
    for plan, metrics_list in by_plan.items():
        retention_rates = [float(m.get("retention_rate") or 0) for m in metrics_list]
        value_scores = [float(m.get("value_realization_score") or 0) for m in metrics_list]
        avg_retention = round(sum(retention_rates) / len(retention_rates), 3) if retention_rates else 0.0
        avg_value = round(sum(value_scores) / len(value_scores), 3) if value_scores else 0.0
        if avg_retention < 0.5:
            churn_indicators.append({"plan": plan, "signal": "low_retention_rate", "severity": "medium"})
        plan_rows.append(
            {
                "plan": plan,
                "retention_rate": avg_retention,
                "value_realization_score": avg_value,
                "fix_320_growth_reference": {"module": "FIX 320", "read_only": True},
                "fix_321_product_market_fit_reference": {"module": "FIX 321", "read_only": True},
                "fix_323_value_realization_reference": {"module": "FIX 323", "read_only": True},
            }
        )

    return {
        "report_id": "commercial-retention-report",
        "program_session_id": program_session_id,
        "plans": plan_rows,
        "churn_indicators": churn_indicators,
        "retention_by_plan_demonstrated": bool(plan_rows),
        "composed_from_fix_320_321_323": True,
        "read_only": True,
    }


def build_commercial_expansion_report(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    workspace_growth = 0
    project_growth = 0
    provider_expansion: set[str] = set()
    plan_expansion_signals = 0

    for customer in cohort:
        customer_sid = str(customer.get("customer_session_id") or "")
        runs = _customer_runs(customer_sid)
        workspace_growth += sum(
            1 for run in runs if (run.get("stage_results") or {}).get("workspace")
        )
        project_growth += len({run.get("request_type") for run in runs if run.get("request_type")})
        provider = str(customer.get("provider") or "")
        if provider:
            provider_expansion.add(provider)
        plan = _normalize_plan(str(customer.get("plan") or "FREE"))
        metrics = _customer_metrics(customer_sid)
        if metrics.get("retention_rate", 0) >= 0.5 and plan != "ENTERPRISE":
            plan_expansion_signals += 1

    cohort_size = len(cohort) or 1
    return {
        "report_id": "commercial-expansion-report",
        "program_session_id": program_session_id,
        "workspace_growth": workspace_growth,
        "project_growth": project_growth,
        "provider_expansion": sorted(provider_expansion),
        "plan_expansion_signals": plan_expansion_signals,
        "expansion_rate": round(plan_expansion_signals / cohort_size, 3),
        "read_only": True,
    }


def build_value_to_revenue_report(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    rows = []
    for customer in cohort:
        plan = _normalize_plan(str(customer.get("plan") or "FREE"))
        customer_sid = str(customer.get("customer_session_id") or "")
        metrics = _customer_metrics(customer_sid)
        realized = float(metrics.get("value_realization_score") or 0)
        perceived = min(1.0, realized + 0.1) if metrics.get("customer_satisfaction_trend") == "positive" else realized
        limits = plan_limits(plan)
        usage = usage_within_limits(
            plan=plan,
            usage={
                "workspaces": len(_customer_runs(customer_sid)),
                "executions": int(metrics.get("adoption_rate", 0) * 10),
            },
        )
        aligned = realized >= 0.5 and bool(usage.get("within_all_limits", True))
        rows.append(
            {
                "customer_id": customer.get("customer_id"),
                "plan": plan,
                "realized_value": round(realized, 3),
                "perceived_value": round(perceived, 3),
                "commercial_plan_alignment": aligned,
                "plan_limits_reference": limits,
            }
        )

    alignment_rate = round(
        sum(1 for row in rows if row.get("commercial_plan_alignment")) / (len(rows) or 1),
        3,
    )
    return {
        "report_id": "value-to-revenue-report",
        "program_session_id": program_session_id,
        "customers": rows,
        "commercial_plan_alignment_rate": alignment_rate,
        "billing_mutation_performed": False,
        "read_only": True,
    }


def build_commercial_friction_report(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    friction: list[dict[str, Any]] = []
    for customer in cohort:
        plan = _normalize_plan(str(customer.get("plan") or "FREE"))
        customer_sid = str(customer.get("customer_session_id") or "")
        metrics = _customer_metrics(customer_sid)
        usage = {"executions": int(float(metrics.get("adoption_rate") or 0) * 10)}
        gaps = commercial_governance_gaps(
            commercial_plan=plan,
            usage=usage,
            billing_identity_complete=bool(customer.get("billing_identity_complete")),
        )
        if plan == "FREE" and metrics.get("retention_rate", 0) >= 0.5:
            friction.append(
                {
                    "category": "pricing",
                    "customer_id": customer.get("customer_id"),
                    "detail": "Sustained value on free tier may indicate upgrade packaging opportunity",
                }
            )
        for gap in gaps:
            category = "entitlement"
            gap_name = str(gap.get("gap") or "")
            if "billing_identity" in gap_name:
                category = "onboarding"
            elif "usage" in gap_name:
                category = "onboarding"
            elif "subscription" in gap_name:
                category = "pricing"
            friction.append(
                {
                    "category": category,
                    "customer_id": customer.get("customer_id"),
                    "detail": gap_name,
                    "severity": gap.get("severity"),
                }
            )
        if customer.get("provider") and plan == "FREE":
            friction.append(
                {
                    "category": "provider_access",
                    "customer_id": customer.get("customer_id"),
                    "detail": "Provider usage on free tier — verify entitlement alignment",
                }
            )

    return {
        "report_id": "commercial-friction-report",
        "program_session_id": program_session_id,
        "friction_count": len(friction),
        "pricing_friction": [f for f in friction if f.get("category") == "pricing"],
        "entitlement_friction": [f for f in friction if f.get("category") == "entitlement"],
        "onboarding_friction": [f for f in friction if f.get("category") == "onboarding"],
        "provider_access_friction": [f for f in friction if f.get("category") == "provider_access"],
        "friction_items": friction[:20],
        "read_only": True,
    }


def build_commercial_opportunity_registry(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    pricing: list[dict[str, Any]] = []
    packaging: list[dict[str, Any]] = []
    retention: list[dict[str, Any]] = []
    expansion: list[dict[str, Any]] = []

    for customer in cohort:
        plan = _normalize_plan(str(customer.get("plan") or "FREE"))
        customer_sid = str(customer.get("customer_session_id") or "")
        metrics = _customer_metrics(customer_sid)
        for opportunity in upgrade_opportunities(plan=plan):
            expansion.append(
                {
                    "customer_id": customer.get("customer_id"),
                    "current_plan": plan,
                    "opportunity": opportunity,
                }
            )
        analytics = commercial_analytics(commercial_plan=plan, org_count=1)
        if analytics.get("trial_adoption") and metrics.get("retention_rate", 0) >= 0.5:
            packaging.append(
                {
                    "customer_id": customer.get("customer_id"),
                    "detail": "Trial-to-paid packaging opportunity",
                    "plan": plan,
                }
            )
        if metrics.get("retention_rate", 0) < 0.5:
            retention.append(
                {
                    "customer_id": customer.get("customer_id"),
                    "detail": "Retention intervention opportunity",
                    "plan": plan,
                }
            )
        if metrics.get("value_realization_score", 0) >= 0.5 and plan == "FREE":
            pricing.append(
                {
                    "customer_id": customer.get("customer_id"),
                    "detail": "Value realization exceeds free tier positioning",
                    "plan": plan,
                }
            )

    opportunities = pricing + packaging + retention + expansion
    return {
        "registry_id": "commercial-opportunity-registry",
        "program_session_id": program_session_id,
        "opportunity_count": len(opportunities),
        "pricing_opportunities": pricing,
        "packaging_opportunities": packaging,
        "retention_opportunities": retention,
        "expansion_opportunities": expansion[:10],
        "automatic_plan_changes_performed": False,
        "read_only": True,
    }


def compute_commercial_metrics(*, program_session_id: str) -> dict[str, Any]:
    adoption = build_adoption_to_plan_report(program_session_id=program_session_id)
    retention = build_commercial_retention_report(program_session_id=program_session_id)
    expansion = build_commercial_expansion_report(program_session_id=program_session_id)
    value = build_value_to_revenue_report(program_session_id=program_session_id)

    plan_rows = adoption.get("plans") or []
    retention_rows = retention.get("plans") or []
    activation_rates = [float(row.get("activation_rate") or 0) for row in plan_rows]
    retention_rates = [float(row.get("retention_rate") or 0) for row in retention_rows]
    value_scores = [float(row.get("value_realization_score") or 0) for row in retention_rows]

    avg_activation = round(sum(activation_rates) / len(activation_rates), 3) if activation_rates else 0.0
    avg_retention = round(sum(retention_rates) / len(retention_rates), 3) if retention_rates else 0.0
    avg_value = round(sum(value_scores) / len(value_scores), 3) if value_scores else 0.0
    plan_adoption = round(len(plan_rows) / max(len(COMMERCIAL_PLANS), 1), 3)
    plan_conversion = round(
        sum(1 for row in plan_rows if row.get("plan") != "FREE") / (len(plan_rows) or 1),
        3,
    )
    sustainability = round(
        (avg_retention + avg_value + float(value.get("commercial_plan_alignment_rate") or 0)) / 3,
        3,
    )

    return {
        "activation_rate": avg_activation,
        "retention_rate": avg_retention,
        "expansion_rate": expansion.get("expansion_rate", 0.0),
        "plan_adoption": plan_adoption,
        "plan_conversion": plan_conversion,
        "value_realization_score": avg_value,
        "commercial_sustainability_score": sustainability,
        "read_only": True,
    }


def register_commercial_cohort_customer_from_text(*, program_session_id: str, body: str) -> dict[str, Any]:
    kv = _parse_kv_blob(body)
    customer_id = kv.get("customer_id") or kv.get("customer") or (
        f"commercial-{len(_cohort_entries(program_session_id=program_session_id)) + 1}"
    )
    entry = register_commercial_cohort_customer(
        entry={
            "customer_id": customer_id,
            "program_session_id": program_session_id,
            "customer_session_id": kv.get("customer_session_id") or kv.get("session_id") or f"{program_session_id}-{customer_id}"[:64],
            "segment": kv.get("segment") or "general",
            "plan": _normalize_plan(kv.get("plan") or "FREE"),
            "environment": kv.get("environment") or kv.get("env") or "staging",
            "use_case": kv.get("use_case") or kv.get("type") or "health_check_endpoint",
            "provider": kv.get("provider") or "Railway",
            "billing_identity_complete": kv.get("billing_identity_complete", "").lower() == "true",
        }
    )
    from aethos_core.workstreams.commercial_validation_program.commercial_validation_program_store import (
        append_commercial_validation_record,
    )

    append_commercial_validation_record(
        session_id=program_session_id,
        kind="commercial_cohort_entry",
        content=body,
        metadata=entry,
    )
    return entry
