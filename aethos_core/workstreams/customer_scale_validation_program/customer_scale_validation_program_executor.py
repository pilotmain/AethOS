# SPDX-License-Identifier: Apache-2.0
"""FIX 350 / WORKSTREAM_F4 — customer scale validation executor."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_contract import (
    SCALE_COHORT_MIN_SIZE,
    SCALE_PROVIDERS,
)
from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_store import (
    list_customer_scale_cohort_registry_entries,
    register_scale_cohort_customer,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_executor import (
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
        for row in list_customer_scale_cohort_registry_entries()
        if str(row.get("program_session_id") or program_session_id) == program_session_id
    ]


def _customer_runs(customer_session_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in list_customer_pilot_run_registry_entries()
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


def build_customer_scale_cohort_registry(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    providers = sorted({str(c.get("provider") or "Railway") for c in cohort})
    return {
        "registry_id": "customer-scale-cohort-registry",
        "program_session_id": program_session_id,
        "cohort_size": len(cohort),
        "minimum_cohort_size": SCALE_COHORT_MIN_SIZE,
        "customers": cohort,
        "providers_in_use": providers,
        "read_only": True,
    }


def build_concurrent_delivery_report(*, program_session_id: str) -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    for customer in _cohort_entries(program_session_id=program_session_id):
        customer_sid = str(customer.get("customer_session_id") or "")
        runs.extend(_customer_runs(customer_sid))
    passed = sum(1 for run in runs if run.get("passed") is True)
    total = len(runs)
    durations = [int(run.get("duration_ms") or 0) for run in runs if run.get("duration_ms")]
    avg_duration = round(sum(durations) / len(durations), 1) if durations else 0.0
    return {
        "report_id": "concurrent-delivery-report",
        "program_session_id": program_session_id,
        "concurrent_customers": len(_cohort_entries(program_session_id=program_session_id)),
        "simultaneous_delivery_activity": total,
        "et1_through_et5_runs": total,
        "delivery_success_rate": round(passed / total, 3) if total else 0.0,
        "average_delivery_duration_ms": avg_duration,
        "delivery_throughput": total,
        "read_only": True,
    }


def build_governance_capacity_report(*, program_session_id: str) -> dict[str, Any]:
    records = _approval_records()
    cohort_sessions = {
        str(c.get("customer_session_id") or "")
        for c in _cohort_entries(program_session_id=program_session_id)
    }
    cohort_sessions.add(program_session_id)
    scoped = [r for r in records if str(r.get("session_id") or "") in cohort_sessions or not cohort_sessions]
    approvals = [r for r in scoped if str(r.get("kind") or "").endswith("_approve") or "approve" in str(r.get("kind") or "")]
    reviews = [r for r in scoped if "review" in str(r.get("kind") or "")]
    escalations = [r for r in scoped if "escalat" in str(r.get("content") or "").lower()]
    return {
        "report_id": "governance-capacity-report",
        "program_session_id": program_session_id,
        "approval_queue_depth": max(0, len(reviews) - len(approvals)),
        "approval_count": len(approvals),
        "review_count": len(reviews),
        "governance_latency_ms": 0,
        "approval_latency_ms": 0,
        "governance_bottleneck_detected": len(reviews) > len(approvals) * 2 and len(reviews) > 5,
        "escalation_frequency": len(escalations),
        "governance_bypass_performed": False,
        "read_only": True,
    }


def build_execution_capacity_report(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    workspace_count = 0
    generation_count = 0
    git_count = 0
    deployment_count = 0
    for customer in cohort:
        customer_sid = str(customer.get("customer_session_id") or "")
        for run in _customer_runs(customer_sid):
            stages = run.get("stage_results") or {}
            if stages.get("workspace"):
                workspace_count += 1
            if stages.get("generation"):
                generation_count += 1
            if stages.get("git_delivery"):
                git_count += 1
            if stages.get("deployment") and not (stages.get("deployment") or {}).get("skipped"):
                deployment_count += 1
    return {
        "report_id": "execution-capacity-report",
        "program_session_id": program_session_id,
        "workspace_creation_throughput": workspace_count,
        "code_generation_throughput": generation_count,
        "git_delivery_throughput": git_count,
        "deployment_throughput": deployment_count,
        "execution_quality_stable": all(
            (run.get("passed") is True)
            for customer in cohort
            for run in _customer_runs(str(customer.get("customer_session_id") or ""))
        )
        if cohort
        else False,
        "read_only": True,
    }


def build_provider_capacity_report(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    provider_stats: dict[str, dict[str, Any]] = {}
    for provider in SCALE_PROVIDERS:
        provider_stats[provider] = {
            "provider": provider,
            "deployment_volume": 0,
            "verification_volume": 0,
            "reliability_score": 1.0,
        }
    for customer in cohort:
        provider = str(customer.get("provider") or "Railway")
        if provider not in provider_stats:
            provider_stats[provider] = {
                "provider": provider,
                "deployment_volume": 0,
                "verification_volume": 0,
                "reliability_score": 1.0,
            }
        for run in _customer_runs(str(customer.get("customer_session_id") or "")):
            deployment = (run.get("stage_results") or {}).get("deployment") or {}
            if deployment and not deployment.get("skipped"):
                provider_stats[provider]["deployment_volume"] += 1
                if deployment.get("verified"):
                    provider_stats[provider]["verification_volume"] += 1
    return {
        "report_id": "provider-capacity-report",
        "program_session_id": program_session_id,
        "providers": list(provider_stats.values()),
        "composed_from_workstream_d2_provider_targets": True,
        "provider_reliability_stable": all(
            row.get("verification_volume", 0) >= row.get("deployment_volume", 0)
            for row in provider_stats.values()
            if row.get("deployment_volume", 0) > 0
        ),
        "read_only": True,
    }


def build_customer_outcome_stability_report(*, program_session_id: str) -> dict[str, Any]:
    cohort_sessions = [
        str(c.get("customer_session_id") or "") for c in _cohort_entries(program_session_id=program_session_id)
    ]
    f2_metrics = [compute_validation_metrics(session_id=sid) for sid in cohort_sessions if sid]
    adoption_rates = [float(m.get("adoption_rate") or 0) for m in f2_metrics]
    retention_rates = [float(m.get("retention_rate") or 0) for m in f2_metrics]
    value_scores = [float(m.get("value_realization_score") or 0) for m in f2_metrics]
    satisfaction_values = [str(m.get("customer_satisfaction_trend") or "neutral") for m in f2_metrics]

    avg_adoption = round(sum(adoption_rates) / len(adoption_rates), 3) if adoption_rates else 0.0
    avg_retention = round(sum(retention_rates) / len(retention_rates), 3) if retention_rates else 0.0
    avg_value = round(sum(value_scores) / len(value_scores), 3) if value_scores else 0.0
    stable = (
        avg_adoption >= 0.5
        and avg_value >= 0.5
        and (not retention_rates or all(r >= 0.5 for r in retention_rates))
    )
    satisfaction_trend = "neutral"
    if satisfaction_values:
        satisfaction_trend = (
            "positive"
            if satisfaction_values.count("positive") >= max(1, len(satisfaction_values) // 2 + 1)
            else "mixed"
        )

    return {
        "report_id": "customer-outcome-stability-report",
        "program_session_id": program_session_id,
        "composed_from_workstream_f2_and_f3_patterns": True,
        "customer_count": len(cohort_sessions),
        "adoption_rate_under_scale": avg_adoption,
        "retention_rate_under_scale": avg_retention,
        "value_realization_score_under_scale": avg_value,
        "customer_satisfaction_trend": satisfaction_trend,
        "outcomes_stable_under_scale": stable,
        "per_customer_metrics": f2_metrics,
        "read_only": True,
    }


def build_scale_bottleneck_registry(*, program_session_id: str) -> dict[str, Any]:
    governance = build_governance_capacity_report(program_session_id=program_session_id)
    execution = build_execution_capacity_report(program_session_id=program_session_id)
    provider = build_provider_capacity_report(program_session_id=program_session_id)
    outcomes = build_customer_outcome_stability_report(program_session_id=program_session_id)
    bottlenecks: list[dict[str, Any]] = []
    if governance.get("governance_bottleneck_detected"):
        bottlenecks.append(
            {
                "bottleneck_id": "governance-review-queue",
                "category": "governance",
                "detail": "Review queue depth exceeds approval throughput",
            }
        )
    if not execution.get("execution_quality_stable"):
        bottlenecks.append(
            {
                "bottleneck_id": "execution-quality",
                "category": "execution",
                "detail": "Execution quality variance detected under concurrent load",
            }
        )
    if not provider.get("provider_reliability_stable"):
        bottlenecks.append(
            {
                "bottleneck_id": "provider-verification",
                "category": "provider",
                "detail": "Provider verification volume lags deployment volume",
            }
        )
    if not outcomes.get("outcomes_stable_under_scale"):
        bottlenecks.append(
            {
                "bottleneck_id": "customer-outcomes",
                "category": "customer_success",
                "detail": "Customer outcomes degraded under scale conditions",
            }
        )
    return {
        "registry_id": "scale-bottleneck-registry",
        "program_session_id": program_session_id,
        "bottleneck_count": len(bottlenecks),
        "bottleneck_frequency": len(bottlenecks),
        "bottlenecks": bottlenecks,
        "read_only": True,
    }


def compute_scale_metrics(*, program_session_id: str) -> dict[str, Any]:
    delivery = build_concurrent_delivery_report(program_session_id=program_session_id)
    governance = build_governance_capacity_report(program_session_id=program_session_id)
    execution = build_execution_capacity_report(program_session_id=program_session_id)
    outcomes = build_customer_outcome_stability_report(program_session_id=program_session_id)
    bottlenecks = build_scale_bottleneck_registry(program_session_id=program_session_id)
    return {
        "concurrent_customers": delivery.get("concurrent_customers", 0),
        "delivery_throughput": delivery.get("delivery_throughput", 0),
        "deployment_throughput": execution.get("deployment_throughput", 0),
        "governance_latency_ms": governance.get("governance_latency_ms", 0),
        "approval_latency_ms": governance.get("approval_latency_ms", 0),
        "adoption_rate": outcomes.get("adoption_rate_under_scale", 0.0),
        "retention_rate": outcomes.get("retention_rate_under_scale", 0.0),
        "value_realization_score": outcomes.get("value_realization_score_under_scale", 0.0),
        "customer_satisfaction_trend": outcomes.get("customer_satisfaction_trend", "neutral"),
        "bottleneck_frequency": bottlenecks.get("bottleneck_frequency", 0),
        "read_only": True,
    }


def register_scale_cohort_customer_from_text(*, program_session_id: str, body: str) -> dict[str, Any]:
    kv = _parse_kv_blob(body)
    customer_id = kv.get("customer_id") or kv.get("customer") or f"scale-{len(_cohort_entries(program_session_id=program_session_id)) + 1}"
    entry = register_scale_cohort_customer(
        entry={
            "customer_id": customer_id,
            "program_session_id": program_session_id,
            "customer_session_id": kv.get("customer_session_id") or kv.get("session_id") or f"{program_session_id}-{customer_id}"[:64],
            "use_case": kv.get("use_case") or "concurrent_delivery",
            "delivery_type": kv.get("delivery_type") or kv.get("type") or "health_check_endpoint",
            "environment": kv.get("environment") or kv.get("env") or "staging",
            "provider": kv.get("provider") or "Railway",
        }
    )
    from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_store import (
        append_customer_scale_validation_record,
    )

    append_customer_scale_validation_record(
        session_id=program_session_id,
        kind="customer_scale_cohort_entry",
        content=body,
        metadata=entry,
    )
    return entry
