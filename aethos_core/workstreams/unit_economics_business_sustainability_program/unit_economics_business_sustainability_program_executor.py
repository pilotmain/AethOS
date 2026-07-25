# SPDX-License-Identifier: Apache-2.0
"""FIX 352 / WORKSTREAM_F6 — unit economics & business sustainability executor."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_executor import (
    compute_validation_metrics,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_store import (
    list_usage_observation_registry_entries,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_store import (
    list_customer_pilot_run_registry_entries,
)
from aethos_core.workstreams.unit_economics_business_sustainability_program.unit_economics_business_sustainability_program_contract import (
    ECONOMIC_COHORT_MIN_SIZE,
    ET_COST_STAGES,
)
from aethos_core.workstreams.unit_economics_business_sustainability_program.unit_economics_business_sustainability_program_store import (
    list_economic_cohort_registry_entries,
    register_economic_cohort_customer,
)


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in re.finditer(r"(\w+)\s*=\s*([^,]+?)(?=,\s*\w+\s*=|$)", blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def _cohort_entries(*, program_session_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in list_economic_cohort_registry_entries()
        if str(row.get("program_session_id") or program_session_id) == program_session_id
    ]


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


def _stage_cost_units(stage: dict[str, Any] | None, *, base: int = 1) -> int:
    if not stage or stage.get("skipped"):
        return 0
    duration_ms = int(stage.get("duration_ms") or 0)
    duration_units = max(1, duration_ms // 1000) if duration_ms else base
    return base + duration_units


def _delivery_cost_for_run(run: dict[str, Any]) -> dict[str, Any]:
    stages = run.get("stage_results") or {}
    workspace = _stage_cost_units(stages.get("workspace"), base=1)
    generation = _stage_cost_units(stages.get("generation"), base=2)
    git_delivery = _stage_cost_units(stages.get("git_delivery"), base=1)
    deployment_stage = stages.get("deployment") or {}
    deployment = _stage_cost_units(deployment_stage, base=2)
    certification = 1 if run.get("passed") is True else 0
    total = workspace + generation + git_delivery + deployment + certification
    return {
        "workspace_cost_units": workspace,
        "code_generation_cost_units": generation,
        "git_delivery_cost_units": git_delivery,
        "deployment_cost_units": deployment,
        "certification_cost_units": certification,
        "total_delivery_cost_units": total,
        "estimated_not_actual_currency": True,
    }


def build_economic_cohort_registry(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    segments = sorted({str(c.get("segment") or "general") for c in cohort})
    plans = sorted({str(c.get("plan") or "FREE") for c in cohort})
    providers = sorted({str(c.get("provider") or "Railway") for c in cohort})
    return {
        "registry_id": "economic-cohort-registry",
        "program_session_id": program_session_id,
        "cohort_size": len(cohort),
        "minimum_cohort_size": ECONOMIC_COHORT_MIN_SIZE,
        "customers": cohort,
        "segments": segments,
        "plans_in_use": plans,
        "providers_in_use": providers,
        "read_only": True,
    }


def build_delivery_cost_report(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    per_customer: list[dict[str, Any]] = []
    totals = {
        "workspace_cost_units": 0,
        "code_generation_cost_units": 0,
        "git_delivery_cost_units": 0,
        "deployment_cost_units": 0,
        "certification_cost_units": 0,
        "total_delivery_cost_units": 0,
    }
    for customer in cohort:
        customer_sid = str(customer.get("customer_session_id") or "")
        customer_total = dict(totals)
        customer_total = {key: 0 for key in customer_total}
        for run in _customer_runs(customer_sid):
            costs = _delivery_cost_for_run(run)
            for key in customer_total:
                customer_total[key] += costs.get(key, 0)
        for key in totals:
            totals[key] += customer_total[key]
        per_customer.append(
            {
                "customer_id": customer.get("customer_id"),
                "deployment_profile": customer.get("deployment_profile") or customer.get("use_case"),
                "provider": customer.get("provider"),
                **customer_total,
            }
        )

    return {
        "report_id": "delivery-cost-report",
        "program_session_id": program_session_id,
        "composed_from_et1_through_et5": True,
        "et_stages_tracked": [stage for _, stage in ET_COST_STAGES],
        "totals": totals,
        "per_customer": per_customer,
        "delivery_economics_sustainable": totals["total_delivery_cost_units"] > 0,
        "estimated_cost_units_only": True,
        "read_only": True,
    }


def build_customer_success_cost_report(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    rows: list[dict[str, Any]] = []
    total_onboarding = 0
    total_support = 0
    total_validation = 0

    for customer in cohort:
        customer_sid = str(customer.get("customer_session_id") or "")
        runs = _customer_runs(customer_sid)
        observations = _usage_observations(customer_sid)
        support_profile = str(customer.get("support_profile") or "standard")
        onboarding_units = 2 + (1 if runs else 0)
        support_units = len(observations) + (2 if support_profile == "high_touch" else 1)
        validation_units = 1 + len(runs)
        total_onboarding += onboarding_units
        total_support += support_units
        total_validation += validation_units
        rows.append(
            {
                "customer_id": customer.get("customer_id"),
                "support_profile": support_profile,
                "onboarding_effort_units": onboarding_units,
                "support_effort_units": support_units,
                "validation_effort_units": validation_units,
                "fix_310_customer_success_reference": {"module": "FIX 310", "read_only": True},
                "fix_319_feedback_reference": {"module": "FIX 319", "read_only": True},
                "composed_from_workstreams_f1_through_f5": True,
            }
        )

    return {
        "report_id": "customer-success-cost-report",
        "program_session_id": program_session_id,
        "onboarding_effort_units": total_onboarding,
        "support_effort_units": total_support,
        "validation_effort_units": total_validation,
        "total_customer_success_cost_units": total_onboarding + total_support + total_validation,
        "per_customer": rows,
        "support_economics_sustainable": total_support <= total_onboarding * 3 + len(cohort) * 5,
        "estimated_cost_units_only": True,
        "read_only": True,
    }


def build_retention_economics_report(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    retention_strengths: list[float] = []
    expansion_likelihoods: list[float] = []
    churn_indicators: list[dict[str, Any]] = []
    plan_expansion_signals = 0

    for customer in cohort:
        customer_sid = str(customer.get("customer_session_id") or "")
        metrics = compute_validation_metrics(session_id=customer_sid)
        retention = float(metrics.get("retention_rate") or 0)
        retention_strengths.append(retention)
        repeat = float(metrics.get("repeat_usage_rate") or 0)
        expansion_likelihoods.append(1.0 if retention >= 0.5 and repeat >= 0.5 else 0.5)
        if retention < 0.5:
            churn_indicators.append(
                {
                    "customer_id": customer.get("customer_id"),
                    "plan": customer.get("plan"),
                    "signal": "low_retention_rate",
                }
            )
        plan = str(customer.get("plan") or "FREE")
        if retention >= 0.5 and plan != "ENTERPRISE":
            plan_expansion_signals += 1

    avg_retention = round(sum(retention_strengths) / len(retention_strengths), 3) if retention_strengths else 0.0
    avg_expansion = round(sum(expansion_likelihoods) / len(expansion_likelihoods), 3) if expansion_likelihoods else 0.0
    expansion_rate = round(plan_expansion_signals / (len(cohort) or 1), 3)

    return {
        "report_id": "retention-economics-report",
        "program_session_id": program_session_id,
        "retention_strength": avg_retention,
        "expansion_likelihood": avg_expansion,
        "expansion_rate_signal": expansion_rate,
        "churn_indicators": churn_indicators,
        "composed_from_fix_320_321_323_and_f5_patterns": True,
        "retention_economics_sustainable": avg_retention >= 0.5,
        "read_only": True,
    }


def build_unit_economics_report(*, program_session_id: str) -> dict[str, Any]:
    delivery = build_delivery_cost_report(program_session_id=program_session_id)
    success = build_customer_success_cost_report(program_session_id=program_session_id)
    retention = build_retention_economics_report(program_session_id=program_session_id)
    cohort = _cohort_entries(program_session_id=program_session_id)

    value_delivered = 0.0
    for customer in cohort:
        customer_sid = str(customer.get("customer_session_id") or "")
        metrics = compute_validation_metrics(session_id=customer_sid)
        value_delivered += float(metrics.get("value_realization_score") or 0)

    avg_value = round(value_delivered / (len(cohort) or 1), 3)
    operating_cost = float((delivery.get("totals") or {}).get("total_delivery_cost_units") or 0)
    support_burden = float(success.get("total_customer_success_cost_units") or 0)
    total_cost = operating_cost + support_burden
    value_to_cost = round(avg_value / max(total_cost, 1), 3)
    sustainability = round(
        (avg_value + float(retention.get("retention_strength") or 0) + value_to_cost) / 3,
        3,
    )

    return {
        "report_id": "unit-economics-report",
        "program_session_id": program_session_id,
        "estimated_value_delivered_score": avg_value,
        "estimated_operating_cost_units": operating_cost,
        "estimated_support_burden_units": support_burden,
        "estimated_total_cost_units": total_cost,
        "sustainability_score": sustainability,
        "value_to_cost_ratio": value_to_cost,
        "estimated_not_actual_currency": True,
        "financial_forecasting_presented_as_fact": False,
        "read_only": True,
    }


def build_economic_friction_report(*, program_session_id: str) -> dict[str, Any]:
    delivery = build_delivery_cost_report(program_session_id=program_session_id)
    success = build_customer_success_cost_report(program_session_id=program_session_id)
    unit = build_unit_economics_report(program_session_id=program_session_id)
    cohort = _cohort_entries(program_session_id=program_session_id)
    friction: list[dict[str, Any]] = []

    avg_delivery = float((delivery.get("totals") or {}).get("total_delivery_cost_units") or 0) / max(len(cohort), 1)
    for row in delivery.get("per_customer") or []:
        customer_cost = float(row.get("total_delivery_cost_units") or 0)
        if customer_cost > avg_delivery * 1.5 and customer_cost > 0:
            friction.append(
                {
                    "category": "expensive_delivery_pattern",
                    "customer_id": row.get("customer_id"),
                    "detail": "Delivery cost exceeds cohort average",
                }
            )

    for row in success.get("per_customer") or []:
        if int(row.get("support_effort_units") or 0) >= 4:
            friction.append(
                {
                    "category": "high_support_customer",
                    "customer_id": row.get("customer_id"),
                    "detail": "Elevated support effort units",
                }
            )

    if float(unit.get("sustainability_score") or 0) < 0.5:
        friction.append(
            {
                "category": "low_value_activity",
                "detail": "Unit economics sustainability score below threshold",
            }
        )

    if avg_delivery > 20:
        friction.append(
            {
                "category": "high_cost_workflow",
                "detail": "Average delivery cost units elevated across cohort",
            }
        )

    return {
        "report_id": "economic-friction-report",
        "program_session_id": program_session_id,
        "friction_count": len(friction),
        "high_cost_workflows": [f for f in friction if f.get("category") == "high_cost_workflow"],
        "high_support_customers": [f for f in friction if f.get("category") == "high_support_customer"],
        "expensive_delivery_patterns": [f for f in friction if f.get("category") == "expensive_delivery_pattern"],
        "low_value_activities": [f for f in friction if f.get("category") == "low_value_activity"],
        "friction_items": friction[:20],
        "read_only": True,
    }


def build_business_sustainability_opportunity_registry(*, program_session_id: str) -> dict[str, Any]:
    friction = build_economic_friction_report(program_session_id=program_session_id)
    success = build_customer_success_cost_report(program_session_id=program_session_id)
    delivery = build_delivery_cost_report(program_session_id=program_session_id)

    efficiency: list[dict[str, Any]] = []
    automation: list[dict[str, Any]] = []
    onboarding: list[dict[str, Any]] = []
    support: list[dict[str, Any]] = []

    if float((delivery.get("totals") or {}).get("total_delivery_cost_units") or 0) > len(_cohort_entries(program_session_id=program_session_id)) * 5:
        efficiency.append({"opportunity": "Reduce ET pipeline cost units via stage optimization", "advisory_only": True})
        automation.append({"opportunity": "Automate repetitive ET certification steps", "advisory_only": True})

    if int(success.get("onboarding_effort_units") or 0) > len(_cohort_entries(program_session_id=program_session_id)) * 3:
        onboarding.append({"opportunity": "Streamline onboarding effort for economic cohort", "advisory_only": True})

    for item in friction.get("high_support_customers") or []:
        support.append(
            {
                "customer_id": item.get("customer_id"),
                "opportunity": "Reduce support burden through self-service patterns",
                "advisory_only": True,
            }
        )

    opportunities = efficiency + automation + onboarding + support
    return {
        "registry_id": "business-sustainability-opportunity-registry",
        "program_session_id": program_session_id,
        "opportunity_count": len(opportunities),
        "efficiency_opportunities": efficiency,
        "automation_opportunities": automation,
        "onboarding_opportunities": onboarding,
        "support_opportunities": support,
        "billing_or_pricing_mutation_performed": False,
        "read_only": True,
    }


def compute_economic_metrics(*, program_session_id: str) -> dict[str, Any]:
    delivery = build_delivery_cost_report(program_session_id=program_session_id)
    success = build_customer_success_cost_report(program_session_id=program_session_id)
    retention = build_retention_economics_report(program_session_id=program_session_id)
    unit = build_unit_economics_report(program_session_id=program_session_id)
    cohort_size = len(_cohort_entries(program_session_id=program_session_id)) or 1

    delivery_cost = float((delivery.get("totals") or {}).get("total_delivery_cost_units") or 0)
    support_cost = float(success.get("total_customer_success_cost_units") or 0)
    retention_strength = float(retention.get("retention_strength") or 0)
    expansion_strength = float(retention.get("expansion_rate_signal") or retention.get("expansion_likelihood") or 0)
    sustainability = float(unit.get("sustainability_score") or 0)
    efficiency = round(
        retention_strength / max((delivery_cost + support_cost) / cohort_size, 1),
        3,
    )

    return {
        "delivery_cost": delivery_cost,
        "support_cost": support_cost,
        "retention_strength": retention_strength,
        "expansion_strength": expansion_strength,
        "sustainability_score": sustainability,
        "operational_efficiency_score": efficiency,
        "estimated_cost_units_only": True,
        "read_only": True,
    }


def register_economic_cohort_customer_from_text(*, program_session_id: str, body: str) -> dict[str, Any]:
    kv = _parse_kv_blob(body)
    customer_id = kv.get("customer_id") or kv.get("customer") or (
        f"economic-{len(_cohort_entries(program_session_id=program_session_id)) + 1}"
    )
    entry = register_economic_cohort_customer(
        entry={
            "customer_id": customer_id,
            "program_session_id": program_session_id,
            "customer_session_id": kv.get("customer_session_id") or kv.get("session_id") or f"{program_session_id}-{customer_id}"[:64],
            "segment": kv.get("segment") or "general",
            "plan": (kv.get("plan") or "FREE").strip().upper(),
            "deployment_profile": kv.get("deployment_profile") or kv.get("use_case") or "health_check_endpoint",
            "provider": kv.get("provider") or "Railway",
            "support_profile": kv.get("support_profile") or "standard",
            "environment": kv.get("environment") or kv.get("env") or "staging",
        }
    )
    from aethos_core.workstreams.unit_economics_business_sustainability_program.unit_economics_business_sustainability_program_store import (
        append_business_sustainability_record,
    )

    append_business_sustainability_record(
        session_id=program_session_id,
        kind="economic_cohort_entry",
        content=body,
        metadata=entry,
    )
    return entry
