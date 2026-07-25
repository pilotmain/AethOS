# SPDX-License-Identifier: Apache-2.0
"""FIX 353 / WORKSTREAM_F7 — business operating model validation executor."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.business_operating_model_validation_program.business_operating_model_validation_program_contract import (
    OPERATING_MODEL_COHORT_MIN_SIZE,
    OPERATING_MODEL_PROVIDERS,
)
from aethos_core.workstreams.business_operating_model_validation_program.business_operating_model_validation_program_store import (
    list_operating_model_cohort_registry_entries,
    register_operating_model_cohort_customer,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_executor import (
    compute_validation_metrics,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_store import (
    list_usage_observation_registry_entries,
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
        for row in list_operating_model_cohort_registry_entries()
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


def _approval_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for module_path, list_fn in (
        (
            "aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_store",
            "list_governed_workspace_creation_records",
        ),
        (
            "aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_store",
            "list_governed_code_generation_records",
        ),
        (
            "aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_store",
            "list_governed_git_delivery_records",
        ),
        (
            "aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_store",
            "list_governed_deployment_execution_records",
        ),
        (
            "aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_store",
            "list_governed_end_to_end_delivery_certification_records",
        ),
    ):
        try:
            mod = __import__(module_path, fromlist=[list_fn])
            rows = getattr(mod, list_fn)()
            if isinstance(rows, list):
                records.extend(rows)
        except Exception:
            continue
    return records


def build_operating_model_registry(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    customer_cohorts = [
        {
            "customer_id": c.get("customer_id"),
            "customer_session_id": c.get("customer_session_id"),
            "segment": c.get("segment"),
            "plan": c.get("plan"),
        }
        for c in cohort
    ]
    provider_cohorts = sorted({str(c.get("provider") or "Railway") for c in cohort})
    delivery_cohorts = sorted(
        {str(c.get("delivery_profile") or c.get("use_case") or "health_check_endpoint") for c in cohort}
    )
    support_cohorts = sorted({str(c.get("support_profile") or "standard") for c in cohort})
    return {
        "registry_id": "operating-model-registry",
        "program_session_id": program_session_id,
        "cohort_size": len(cohort),
        "minimum_cohort_size": OPERATING_MODEL_COHORT_MIN_SIZE,
        "customer_cohorts": customer_cohorts,
        "provider_cohorts": provider_cohorts,
        "delivery_cohorts": delivery_cohorts,
        "support_cohorts": support_cohorts,
        "customers": cohort,
        "read_only": True,
    }


def build_delivery_sustainability_report(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    runs: list[dict[str, Any]] = []
    interventions = 0
    for customer in cohort:
        customer_sid = str(customer.get("customer_session_id") or "")
        customer_runs = _customer_runs(customer_sid)
        runs.extend(customer_runs)
        interventions += sum(1 for run in customer_runs if run.get("passed") is not True)

    passed = sum(1 for run in runs if run.get("passed") is True)
    total = len(runs)
    throughput = total
    reliability = round(passed / total, 3) if total else 0.0
    intervention_rate = round(interventions / total, 3) if total else 0.0
    execution_burden = sum(int(run.get("duration_ms") or 0) for run in runs)

    return {
        "report_id": "delivery-sustainability-report",
        "program_session_id": program_session_id,
        "composed_from_et1_through_et5_and_f1_through_f4_patterns": True,
        "throughput": throughput,
        "reliability": reliability,
        "intervention_rate": intervention_rate,
        "execution_burden_ms": execution_burden,
        "delivery_capacity_sustainable": reliability >= 0.8 and total >= OPERATING_MODEL_COHORT_MIN_SIZE,
        "governance_mutation_performed": False,
        "read_only": True,
    }


def build_support_sustainability_report(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    total_effort = 0
    total_volume = 0
    per_customer: list[dict[str, Any]] = []

    for customer in cohort:
        customer_sid = str(customer.get("customer_session_id") or "")
        observations = _usage_observations(customer_sid)
        support_profile = str(customer.get("support_profile") or "standard")
        effort = len(observations) + (2 if support_profile == "high_touch" else 1)
        volume = sum(int(o.get("executions") or 0) for o in observations)
        total_effort += effort
        total_volume += volume
        per_customer.append(
            {
                "customer_id": customer.get("customer_id"),
                "support_profile": support_profile,
                "support_effort_units": effort,
                "support_volume": volume,
                "fix_310_customer_success_reference": {"module": "FIX 310", "read_only": True},
                "fix_319_feedback_reference": {"module": "FIX 319", "read_only": True},
            }
        )

    cohort_size = len(cohort) or 1
    scalability = round(total_volume / max(total_effort, 1), 3)

    return {
        "report_id": "support-sustainability-report",
        "program_session_id": program_session_id,
        "support_effort_units": total_effort,
        "support_volume": total_volume,
        "support_scalability_ratio": scalability,
        "per_customer": per_customer,
        "composed_from_f2_through_f6_patterns": True,
        "support_capacity_sustainable": total_effort <= cohort_size * 6,
        "read_only": True,
    }


def build_governance_sustainability_report(*, program_session_id: str) -> dict[str, Any]:
    cohort_sessions = {
        str(c.get("customer_session_id") or "") for c in _cohort_entries(program_session_id=program_session_id)
    }
    cohort_sessions.add(program_session_id)
    records = _approval_records()
    scoped = [r for r in records if str(r.get("session_id") or "") in cohort_sessions or not cohort_sessions]
    approvals = [r for r in scoped if "approve" in str(r.get("kind") or "")]
    reviews = [r for r in scoped if "review" in str(r.get("kind") or "")]
    approval_burden = max(0, len(reviews) - len(approvals))
    throughput = len(approvals)

    return {
        "report_id": "governance-sustainability-report",
        "program_session_id": program_session_id,
        "approval_burden": approval_burden,
        "review_count": len(reviews),
        "approval_count": len(approvals),
        "governance_throughput": throughput,
        "review_latency_ms": 0,
        "fix_302_identity_access_reference": {"module": "FIX 302", "read_only": True},
        "fix_307_audit_portal_reference": {"module": "FIX 307", "read_only": True},
        "fix_313_launch_operations_reference": {"module": "FIX 313", "read_only": True},
        "governance_capacity_sustainable": approval_burden <= max(throughput, 1),
        "governance_mutation_performed": False,
        "read_only": True,
    }


def build_provider_sustainability_report(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    provider_counts: dict[str, int] = {provider: 0 for provider in OPERATING_MODEL_PROVIDERS}
    deployment_volume = 0
    verification_volume = 0

    for customer in cohort:
        provider = str(customer.get("provider") or "Railway")
        provider_counts[provider] = provider_counts.get(provider, 0) + 1
        for run in _customer_runs(str(customer.get("customer_session_id") or "")):
            deployment = (run.get("stage_results") or {}).get("deployment") or {}
            if deployment and not deployment.get("skipped"):
                deployment_volume += 1
                if deployment.get("verified"):
                    verification_volume += 1

    active_providers = [p for p, count in provider_counts.items() if count > 0]
    concentration = round(max(provider_counts.values()) / max(len(cohort), 1), 3) if cohort else 0.0
    reliability = round(verification_volume / deployment_volume, 3) if deployment_volume else 1.0
    operational_burden = deployment_volume

    return {
        "report_id": "provider-sustainability-report",
        "program_session_id": program_session_id,
        "provider_concentration": concentration,
        "active_providers": active_providers,
        "provider_reliability": reliability,
        "provider_operational_burden": operational_burden,
        "fix_303_provider_connection_reference": {"module": "FIX 303", "read_only": True},
        "composed_from_workstream_d1_d2_patterns": True,
        "provider_capacity_sustainable": reliability >= 0.8 or deployment_volume == 0,
        "provider_mutation_performed": False,
        "read_only": True,
    }


def build_business_sustainability_analysis(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    delivery = build_delivery_sustainability_report(program_session_id=program_session_id)
    support = build_support_sustainability_report(program_session_id=program_session_id)

    value_scores: list[float] = []
    retention_rates: list[float] = []
    for customer in cohort:
        customer_sid = str(customer.get("customer_session_id") or "")
        metrics = compute_validation_metrics(session_id=customer_sid)
        value_scores.append(float(metrics.get("value_realization_score") or 0))
        retention_rates.append(float(metrics.get("retention_rate") or 0))

    avg_value = round(sum(value_scores) / len(value_scores), 3) if value_scores else 0.0
    avg_retention = round(sum(retention_rates) / len(retention_rates), 3) if retention_rates else 0.0
    efficiency = round(
        avg_value
        / max(
            float(delivery.get("execution_burden_ms") or 1) / 1000
            + float(support.get("support_effort_units") or 1),
            1,
        ),
        3,
    )
    cost_burden = float(support.get("support_effort_units") or 0) + float(delivery.get("throughput") or 0)
    sustainability = round((avg_value + avg_retention + efficiency) / 3, 3)

    return {
        "analysis_id": "business-sustainability-analysis",
        "program_session_id": program_session_id,
        "efficiency": efficiency,
        "cost_burden_units": cost_burden,
        "sustainability_indicators": {
            "value_realization_score": avg_value,
            "retention_rate": avg_retention,
            "delivery_reliability": delivery.get("reliability"),
            "support_scalability_ratio": support.get("support_scalability_ratio"),
        },
        "sustainability_score": sustainability,
        "composed_from_workstream_f5_and_f6_patterns": True,
        "pricing_mutation_performed": False,
        "read_only": True,
    }


def build_operating_model_opportunity_registry(*, program_session_id: str) -> dict[str, Any]:
    delivery = build_delivery_sustainability_report(program_session_id=program_session_id)
    governance = build_governance_sustainability_report(program_session_id=program_session_id)
    provider = build_provider_sustainability_report(program_session_id=program_session_id)
    support = build_support_sustainability_report(program_session_id=program_session_id)

    delivery_opps: list[dict[str, Any]] = []
    governance_opps: list[dict[str, Any]] = []
    provider_opps: list[dict[str, Any]] = []
    support_opps: list[dict[str, Any]] = []

    if float(delivery.get("intervention_rate") or 0) > 0.1:
        delivery_opps.append({"opportunity": "Reduce delivery intervention rate", "advisory_only": True})
    if int(governance.get("approval_burden") or 0) > 2:
        governance_opps.append({"opportunity": "Reduce governance approval burden", "advisory_only": True})
    if float(provider.get("provider_concentration") or 0) > 0.6:
        provider_opps.append({"opportunity": "Diversify provider concentration", "advisory_only": True})
    if not support.get("support_capacity_sustainable"):
        support_opps.append({"opportunity": "Improve support scalability patterns", "advisory_only": True})

    opportunities = delivery_opps + governance_opps + provider_opps + support_opps
    return {
        "registry_id": "operating-model-opportunity-registry",
        "program_session_id": program_session_id,
        "opportunity_count": len(opportunities),
        "delivery_opportunities": delivery_opps,
        "governance_opportunities": governance_opps,
        "provider_opportunities": provider_opps,
        "support_opportunities": support_opps,
        "business_automation_performed": False,
        "read_only": True,
    }


def compute_operating_model_metrics(*, program_session_id: str) -> dict[str, Any]:
    delivery = build_delivery_sustainability_report(program_session_id=program_session_id)
    governance = build_governance_sustainability_report(program_session_id=program_session_id)
    support = build_support_sustainability_report(program_session_id=program_session_id)
    provider = build_provider_sustainability_report(program_session_id=program_session_id)
    economic = build_business_sustainability_analysis(program_session_id=program_session_id)

    delivery_efficiency = round(float(delivery.get("reliability") or 0) / max(float(delivery.get("intervention_rate") or 0) + 0.1, 0.1), 3)
    governance_efficiency = round(
        float(governance.get("governance_throughput") or 0) / max(float(governance.get("approval_burden") or 0) + 1, 1),
        3,
    )
    support_efficiency = float(support.get("support_scalability_ratio") or 0)
    provider_efficiency = float(provider.get("provider_reliability") or 0)
    sustainability = float(economic.get("sustainability_score") or 0)
    leverage = round(
        (delivery_efficiency + governance_efficiency + support_efficiency + provider_efficiency) / 4,
        3,
    )

    return {
        "delivery_efficiency": delivery_efficiency,
        "governance_efficiency": governance_efficiency,
        "support_efficiency": support_efficiency,
        "provider_efficiency": provider_efficiency,
        "business_sustainability_score": sustainability,
        "operating_leverage_score": leverage,
        "read_only": True,
    }


def register_operating_model_cohort_customer_from_text(*, program_session_id: str, body: str) -> dict[str, Any]:
    kv = _parse_kv_blob(body)
    customer_id = kv.get("customer_id") or kv.get("customer") or (
        f"operating-{len(_cohort_entries(program_session_id=program_session_id)) + 1}"
    )
    entry = register_operating_model_cohort_customer(
        entry={
            "customer_id": customer_id,
            "program_session_id": program_session_id,
            "customer_session_id": kv.get("customer_session_id") or kv.get("session_id") or f"{program_session_id}-{customer_id}"[:64],
            "segment": kv.get("segment") or "general",
            "plan": (kv.get("plan") or "FREE").strip().upper(),
            "provider": kv.get("provider") or "Railway",
            "delivery_profile": kv.get("delivery_profile") or kv.get("use_case") or "health_check_endpoint",
            "support_profile": kv.get("support_profile") or "standard",
            "environment": kv.get("environment") or kv.get("env") or "staging",
        }
    )
    from aethos_core.workstreams.business_operating_model_validation_program.business_operating_model_validation_program_store import (
        append_operating_model_record,
    )

    append_operating_model_record(
        session_id=program_session_id,
        kind="operating_model_cohort_entry",
        content=body,
        metadata=entry,
    )
    return entry
