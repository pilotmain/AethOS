# SPDX-License-Identifier: Apache-2.0
"""FIX 356 / WORKSTREAM_G3 — revenue density & business viability executor."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_evaluator import (
    is_capability_entitled,
    normalize_commercial_plan,
    plan_capabilities,
    plan_limits,
    upgrade_opportunities,
    usage_within_limits,
)
from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_evaluator import (
    commercial_analytics,
    commercial_governance_gaps,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_executor import (
    build_customer_adoption_report,
    compute_validation_metrics,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_store import (
    list_usage_observation_registry_entries,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_store import (
    list_customer_pilot_run_registry_entries,
)
from aethos_core.workstreams.revenue_density_business_viability_program.revenue_density_business_viability_program_contract import (
    COMMERCIAL_PLANS,
    REVENUE_COHORT_MIN_SIZE,
    REVENUE_MATURITY_LEVELS,
)
from aethos_core.workstreams.revenue_density_business_viability_program.revenue_density_business_viability_program_store import (
    list_revenue_cohort_registry_entries,
    register_revenue_cohort_customer,
)


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in re.finditer(r"(\w+)\s*=\s*([^,]+?)(?=,\s*\w+\s*=|$)", blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def _cohort_entries(*, program_session_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in list_revenue_cohort_registry_entries()
        if str(row.get("program_session_id") or program_session_id) == program_session_id
    ]


def _normalize_plan(plan: str | None) -> str:
    raw = str(plan or "FREE").strip().upper()
    if raw in COMMERCIAL_PLANS:
        return raw
    return normalize_commercial_plan(raw.lower())


def _customer_runs(customer_session_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in list_customer_pilot_run_registry_entries()
        if str(row.get("session_id") or "") == customer_session_id
    ]


def _usage_observations(customer_session_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in list_usage_observation_registry_entries()
        if str(row.get("session_id") or "") == customer_session_id
    ]


def _customer_signals(customer: dict[str, Any]) -> dict[str, Any]:
    customer_sid = str(customer.get("customer_session_id") or "")
    metrics = compute_validation_metrics(session_id=customer_sid) if customer_sid else {}
    adoption = build_customer_adoption_report(session_id=customer_sid) if customer_sid else {}
    observations = _usage_observations(customer_sid)
    runs = _customer_runs(customer_sid)
    plan = _normalize_plan(str(customer.get("plan") or "FREE"))

    usage_executions = sum(int(o.get("executions") or 0) for o in observations)
    adoption_level = str(customer.get("adoption_level") or "")
    if not adoption_level:
        if metrics.get("repeat_usage_rate", 0) >= 0.5 and usage_executions >= 4:
            adoption_level = "dependent"
        elif adoption.get("repeat_use"):
            adoption_level = "adopted"
        elif adoption.get("first_use"):
            adoption_level = "active"
        else:
            adoption_level = "observed"

    usage_level = str(customer.get("usage_level") or "")
    if not usage_level:
        usage_level = "high" if usage_executions >= 6 else "medium" if usage_executions >= 2 else "low"

    retention_level = str(customer.get("retention_level") or "")
    if not retention_level:
        retention = float(metrics.get("retention_rate") or 0)
        retention_level = "strong" if retention >= 0.5 else "weak"

    usage = usage_within_limits(
        plan=plan,
        usage={"workspaces": len(runs), "executions": usage_executions},
    )

    return {
        "customer_id": customer.get("customer_id"),
        "customer_session_id": customer_sid,
        "plan": plan,
        "segment": customer.get("segment") or "general",
        "adoption_level": adoption_level,
        "usage_level": usage_level,
        "retention_level": retention_level,
        "metrics": metrics,
        "usage_executions": usage_executions,
        "workspace_count": len(runs),
        "provider_count": len({customer.get("provider") or "Railway"}),
        "project_count": len({run.get("request_type") for run in runs if run.get("request_type")}),
        "entitlement_within_limits": bool(usage.get("within_all_limits", True)),
        "value_realization_score": float(metrics.get("value_realization_score") or 0),
        "retention_rate": float(metrics.get("retention_rate") or 0),
        "adoption_rate": float(metrics.get("adoption_rate") or 0),
    }


def _revenue_maturity_level(signals: dict[str, Any]) -> str:
    value = float(signals.get("value_realization_score") or 0)
    retention = float(signals.get("retention_rate") or 0)
    usage = int(signals.get("usage_executions") or 0)
    adoption = str(signals.get("adoption_level") or "")

    if retention >= 0.5 and value >= 0.5 and usage >= 6 and adoption in {"adopted", "dependent"}:
        return "sustainable"
    if retention >= 0.5 and value >= 0.5 and usage >= 2:
        return "viable"
    if usage >= 1 or value >= 0.5:
        return "emerging"
    return "potential"


def build_revenue_cohort_registry(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    enriched = [_customer_signals(customer) for customer in cohort]
    return {
        "registry_id": "revenue-cohort-registry",
        "program_session_id": program_session_id,
        "cohort_size": len(cohort),
        "minimum_cohort_size": REVENUE_COHORT_MIN_SIZE,
        "customers": cohort,
        "customer_signals": enriched,
        "segments": sorted({str(c.get("segment") or "general") for c in cohort}),
        "plans_in_use": sorted({_normalize_plan(str(c.get("plan") or "FREE")) for c in cohort}),
        "read_only": True,
    }


def build_plan_utilization_report(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    by_plan: list[dict[str, Any]] = []
    utilization_scores: list[float] = []

    for customer in cohort:
        signals = _customer_signals(customer)
        plan = signals["plan"]
        limits = plan_limits(plan)
        capabilities = plan_capabilities(plan)
        engaged = sum(
            1
            for capability in capabilities[:5]
            if signals.get("usage_executions", 0) > 0 or is_capability_entitled(plan=plan, capability=capability)
        )
        utilization = round(min(1.0, engaged / max(len(capabilities[:5]), 1)), 3)
        utilization_scores.append(utilization)
        by_plan.append(
            {
                "customer_id": signals.get("customer_id"),
                "plan": plan,
                "plan_utilization": utilization,
                "entitlement_utilization": 1.0 if signals.get("entitlement_within_limits") else 0.5,
                "feature_engagement": engaged,
                "fix_305_entitlements_reference": {"module": "FIX 305", "read_only": True},
                "fix_308_payment_readiness_reference": {"module": "FIX 308", "read_only": True},
                "composed_from_f5_and_g2_patterns": True,
            }
        )

    avg_utilization = round(sum(utilization_scores) / len(utilization_scores), 3) if utilization_scores else 0.0

    return {
        "report_id": "plan-utilization-report",
        "program_session_id": program_session_id,
        "plans": by_plan,
        "plan_utilization_score": avg_utilization,
        "plan_engagement_demonstrated": avg_utilization >= 0.5,
        "billing_execution_performed": False,
        "read_only": True,
    }


def build_expansion_potential_report(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    workspace_growth = 0
    provider_growth: set[str] = set()
    project_growth = 0
    upgrade_indicators = 0

    for customer in cohort:
        signals = _customer_signals(customer)
        workspace_growth += int(signals.get("workspace_count") or 0)
        provider_growth.add(str(customer.get("provider") or "Railway"))
        project_growth += int(signals.get("project_count") or 0)
        plan = signals["plan"]
        if signals.get("retention_rate", 0) >= 0.5 and plan != "ENTERPRISE":
            upgrade_indicators += 1
            for opp in upgrade_opportunities(plan=plan):
                if opp.get("advisory_only"):
                    upgrade_indicators += 0  # counted once per customer

    cohort_size = len(cohort) or 1
    expansion_score = round(upgrade_indicators / cohort_size, 3)

    return {
        "report_id": "expansion-potential-report",
        "program_session_id": program_session_id,
        "workspace_growth": workspace_growth,
        "provider_growth": sorted(provider_growth),
        "project_growth": project_growth,
        "plan_upgrade_indicators": upgrade_indicators,
        "expansion_score": expansion_score,
        "expansion_potential_demonstrated": expansion_score > 0,
        "plan_upgrade_performed": False,
        "read_only": True,
    }


def build_retention_value_report(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    retention_rates: list[float] = []
    repeat_usage = 0
    dependence = 0

    for customer in cohort:
        signals = _customer_signals(customer)
        retention_rates.append(float(signals.get("retention_rate") or 0))
        if float(signals.get("metrics", {}).get("repeat_usage_rate") or 0) >= 0.5:
            repeat_usage += 1
        if str(signals.get("adoption_level") or "") in {"adopted", "dependent"}:
            dependence += 1

    avg_retention = round(sum(retention_rates) / len(retention_rates), 3) if retention_rates else 0.0
    cohort_size = len(cohort) or 1

    return {
        "report_id": "retention-value-report",
        "program_session_id": program_session_id,
        "retention_quality": avg_retention,
        "repeat_usage_customers": repeat_usage,
        "customer_dependence_count": dependence,
        "retention_strength": avg_retention,
        "composed_from_f5_f6_and_g2_patterns": True,
        "retention_value_demonstrated": avg_retention >= 0.5,
        "read_only": True,
    }


def build_revenue_signal_report(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    active_signals = 0
    recurring_signals = 0
    expansion_signals = 0
    readiness = 0
    maturity_counts = {level: 0 for level in REVENUE_MATURITY_LEVELS}

    for customer in cohort:
        signals = _customer_signals(customer)
        plan = signals["plan"]
        if signals.get("usage_executions", 0) > 0:
            active_signals += 1
        if signals.get("retention_rate", 0) >= 0.5 and signals.get("usage_executions", 0) >= 2:
            recurring_signals += 1
        if signals.get("retention_rate", 0) >= 0.5 and plan != "ENTERPRISE":
            expansion_signals += 1
        analytics = commercial_analytics(commercial_plan=plan, org_count=1)
        if analytics.get("trial_adoption") or signals.get("value_realization_score", 0) >= 0.5:
            readiness += 1
        level = _revenue_maturity_level(signals)
        maturity_counts[level] = maturity_counts.get(level, 0) + 1

    cohort_size = len(cohort) or 1
    return {
        "report_id": "revenue-signal-report",
        "program_session_id": program_session_id,
        "active_value_signals": active_signals,
        "recurring_value_signals": recurring_signals,
        "expansion_signals": expansion_signals,
        "commercial_readiness_indicators": readiness,
        "revenue_maturity_distribution": maturity_counts,
        "revenue_density_score": round((active_signals + recurring_signals + expansion_signals) / (cohort_size * 3), 3),
        "payment_processing_performed": False,
        "read_only": True,
    }


def build_revenue_friction_report(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    friction: list[dict[str, Any]] = []

    for customer in cohort:
        signals = _customer_signals(customer)
        plan = signals["plan"]
        usage = {"executions": int(signals.get("usage_executions") or 0)}
        gaps = commercial_governance_gaps(
            commercial_plan=plan,
            usage=usage,
            billing_identity_complete=bool(customer.get("billing_identity_complete")),
        )

        if plan == "FREE" and signals.get("value_realization_score", 0) >= 0.5:
            friction.append(
                {
                    "category": "underutilized_plan",
                    "customer_id": signals.get("customer_id"),
                    "detail": "High value on free tier may indicate packaging friction",
                }
            )
        if not signals.get("entitlement_within_limits"):
            friction.append(
                {
                    "category": "entitlement_confusion",
                    "customer_id": signals.get("customer_id"),
                    "detail": "Usage exceeds modeled entitlement limits",
                }
            )
        for gap in gaps:
            category = "onboarding_friction"
            if "subscription" in str(gap.get("gap") or ""):
                category = "upgrade_friction"
            friction.append(
                {
                    "category": category,
                    "customer_id": signals.get("customer_id"),
                    "detail": gap.get("gap"),
                }
            )
        if signals.get("usage_executions", 0) == 0:
            friction.append(
                {
                    "category": "onboarding_friction",
                    "customer_id": signals.get("customer_id"),
                    "detail": "No usage executions recorded",
                }
            )

    return {
        "report_id": "revenue-friction-report",
        "program_session_id": program_session_id,
        "friction_count": len(friction),
        "underutilized_plans": [f for f in friction if f.get("category") == "underutilized_plan"],
        "entitlement_confusion": [f for f in friction if f.get("category") == "entitlement_confusion"],
        "onboarding_friction": [f for f in friction if f.get("category") == "onboarding_friction"],
        "upgrade_friction": [f for f in friction if f.get("category") == "upgrade_friction"],
        "friction_items": friction[:20],
        "read_only": True,
    }


def build_revenue_opportunity_registry(*, program_session_id: str) -> dict[str, Any]:
    friction = build_revenue_friction_report(program_session_id=program_session_id)
    cohort = _cohort_entries(program_session_id=program_session_id)

    packaging: list[dict[str, Any]] = []
    adoption: list[dict[str, Any]] = []
    retention: list[dict[str, Any]] = []
    expansion: list[dict[str, Any]] = []

    for customer in cohort:
        signals = _customer_signals(customer)
        plan = signals["plan"]
        if plan == "FREE" and signals.get("value_realization_score", 0) >= 0.5:
            packaging.append(
                {
                    "customer_id": signals.get("customer_id"),
                    "opportunity": "Packaging opportunity for sustained free-tier value",
                    "advisory_only": True,
                }
            )
        if signals.get("usage_executions", 0) < 2:
            adoption.append(
                {
                    "customer_id": signals.get("customer_id"),
                    "opportunity": "Increase adoption before commercial readiness",
                    "advisory_only": True,
                }
            )
        if signals.get("retention_rate", 0) < 0.5:
            retention.append(
                {
                    "customer_id": signals.get("customer_id"),
                    "opportunity": "Retention intervention before revenue signal maturity",
                    "advisory_only": True,
                }
            )
        for opp in upgrade_opportunities(plan=plan):
            expansion.append(
                {
                    "customer_id": signals.get("customer_id"),
                    "current_plan": plan,
                    "opportunity": opp,
                    "advisory_only": True,
                }
            )

    for item in friction.get("underutilized_plans") or []:
        packaging.append({"source_friction": item, "opportunity": "Review plan positioning", "advisory_only": True})

    opportunities = packaging + adoption + retention + expansion[:10]
    return {
        "registry_id": "revenue-opportunity-registry",
        "program_session_id": program_session_id,
        "opportunity_count": len(opportunities),
        "packaging_opportunities": packaging,
        "adoption_opportunities": adoption,
        "retention_opportunities": retention,
        "expansion_opportunities": expansion[:10],
        "billing_or_plan_mutation_performed": False,
        "read_only": True,
    }


def compute_revenue_density_metrics(*, program_session_id: str) -> dict[str, Any]:
    plan_util = build_plan_utilization_report(program_session_id=program_session_id)
    expansion = build_expansion_potential_report(program_session_id=program_session_id)
    retention = build_retention_value_report(program_session_id=program_session_id)
    revenue = build_revenue_signal_report(program_session_id=program_session_id)
    cohort = _cohort_entries(program_session_id=program_session_id)

    adoption_strength = round(
        sum(1 for c in cohort if _customer_signals(c).get("adoption_rate", 0) >= 0.5) / max(len(cohort), 1),
        3,
    )
    revenue_density = float(revenue.get("revenue_density_score") or 0)
    viability = round(
        (
            float(plan_util.get("plan_utilization_score") or 0)
            + float(expansion.get("expansion_score") or 0)
            + float(retention.get("retention_strength") or 0)
            + adoption_strength
            + revenue_density
        )
        / 5,
        3,
    )

    return {
        "plan_utilization_score": plan_util.get("plan_utilization_score", 0.0),
        "expansion_score": expansion.get("expansion_score", 0.0),
        "retention_strength": retention.get("retention_strength", 0.0),
        "adoption_strength": adoption_strength,
        "revenue_density_score": revenue_density,
        "business_viability_score": viability,
        "read_only": True,
    }


def register_revenue_cohort_customer_from_text(*, program_session_id: str, body: str) -> dict[str, Any]:
    kv = _parse_kv_blob(body)
    customer_id = kv.get("customer_id") or kv.get("customer") or (
        f"revenue-{len(_cohort_entries(program_session_id=program_session_id)) + 1}"
    )
    entry = register_revenue_cohort_customer(
        entry={
            "customer_id": customer_id,
            "program_session_id": program_session_id,
            "customer_session_id": kv.get("customer_session_id") or kv.get("session_id") or f"{program_session_id}-{customer_id}"[:64],
            "segment": kv.get("segment") or "general",
            "plan": _normalize_plan(kv.get("plan") or "FREE"),
            "adoption_level": kv.get("adoption_level") or "",
            "usage_level": kv.get("usage_level") or "",
            "retention_level": kv.get("retention_level") or "",
            "provider": kv.get("provider") or "Railway",
            "billing_identity_complete": kv.get("billing_identity_complete", "").lower() == "true",
        }
    )
    from aethos_core.workstreams.revenue_density_business_viability_program.revenue_density_business_viability_program_store import (
        append_revenue_density_record,
    )

    append_revenue_density_record(
        session_id=program_session_id,
        kind="revenue_cohort_entry",
        content=body,
        metadata=entry,
    )
    return entry
