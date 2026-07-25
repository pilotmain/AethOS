# SPDX-License-Identifier: Apache-2.0
"""FIX 349 / WORKSTREAM_F3 — multi-customer value proof executor."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_executor import (
    build_customer_adoption_report,
    build_customer_retention_report,
    build_customer_value_validation_report,
    compute_validation_metrics,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_store import (
    list_customer_pilot_run_registry_entries,
)
from aethos_core.workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_contract import (
    COHORT_MIN_SIZE,
)
from aethos_core.workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_store import (
    list_customer_cohort_registry_entries,
    register_cohort_customer,
)


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in re.finditer(r"(\w+)\s*=\s*([^,]+?)(?=,\s*\w+\s*=|$)", blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def _cohort_entries(*, program_session_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in list_customer_cohort_registry_entries()
        if str(row.get("program_session_id") or program_session_id) == program_session_id
    ]


def build_customer_cohort_registry(*, program_session_id: str) -> dict[str, Any]:
    cohort = _cohort_entries(program_session_id=program_session_id)
    return {
        "registry_id": "customer-cohort-registry",
        "program_session_id": program_session_id,
        "cohort_size": len(cohort),
        "minimum_cohort_size": COHORT_MIN_SIZE,
        "customers": cohort,
        "read_only": True,
    }


def _customer_runs(customer_session_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in list_customer_pilot_run_registry_entries()
        if str(row.get("session_id") or "") == customer_session_id
    ]


def build_delivery_outcome_registry(*, program_session_id: str) -> dict[str, Any]:
    outcomes = []
    for customer in _cohort_entries(program_session_id=program_session_id):
        customer_sid = str(customer.get("customer_session_id") or customer.get("session_id") or "")
        runs = _customer_runs(customer_sid)
        for run in runs:
            deployment = (run.get("stage_results") or {}).get("deployment") or {}
            outcomes.append(
                {
                    "customer_id": customer.get("customer_id"),
                    "customer_session_id": customer_sid,
                    "run_id": run.get("run_id"),
                    "request_type": run.get("request_type"),
                    "scenario_id": run.get("scenario_id"),
                    "certification_passed": run.get("passed") is True,
                    "deployment_verified": deployment.get("verified") is True,
                    "composed_from_workstream_f1": True,
                }
            )
    passed = sum(1 for row in outcomes if row.get("certification_passed"))
    return {
        "registry_id": "delivery-outcome-registry",
        "program_session_id": program_session_id,
        "outcome_count": len(outcomes),
        "passed_count": passed,
        "outcomes": outcomes,
        "read_only": True,
    }


def _cohort_customer_metrics(program_session_id: str) -> list[dict[str, Any]]:
    rows = []
    for customer in _cohort_entries(program_session_id=program_session_id):
        customer_sid = str(customer.get("customer_session_id") or customer.get("session_id") or "")
        adoption = build_customer_adoption_report(session_id=customer_sid)
        validation = build_customer_value_validation_report(session_id=customer_sid)
        retention = build_customer_retention_report(session_id=customer_sid)
        metrics = compute_validation_metrics(session_id=customer_sid)
        rows.append(
            {
                "customer_id": customer.get("customer_id"),
                "customer_session_id": customer_sid,
                "adoption": adoption,
                "validation": validation,
                "retention": retention,
                "metrics": metrics,
            }
        )
    return rows


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 3) if values else 0.0


def build_cohort_adoption_report(*, program_session_id: str) -> dict[str, Any]:
    rows = _cohort_customer_metrics(program_session_id)
    adoption_rates = [float(r["metrics"].get("adoption_rate") or 0) for r in rows]
    repeat_rates = [float(r["metrics"].get("repeat_usage_rate") or 0) for r in rows]
    abandonment_rates = [float(r["metrics"].get("abandonment_rate") or 0) for r in rows]
    return {
        "report_id": "cohort-adoption-report",
        "program_session_id": program_session_id,
        "customer_count": len(rows),
        "adoption_rate": _avg(adoption_rates),
        "engagement_rate": _avg(repeat_rates),
        "abandonment_rate": _avg(abandonment_rates),
        "repeatable_adoption": all(r["adoption"].get("first_use") for r in rows) if rows else False,
        "per_customer": rows,
        "read_only": True,
    }


def build_cohort_value_report(*, program_session_id: str) -> dict[str, Any]:
    rows = _cohort_customer_metrics(program_session_id)
    scores = [float(r["validation"].get("value_realization_score") or 0) for r in rows]
    aligned = [r["validation"].get("value_aligned") for r in rows]
    return {
        "report_id": "cohort-value-report",
        "program_session_id": program_session_id,
        "value_realization_score": _avg(scores),
        "realized_count": sum(1 for flag in aligned if flag is True),
        "unrealized_count": sum(1 for flag in aligned if flag is False),
        "repeatable_value_realization": all(flag is True for flag in aligned) if aligned else False,
        "per_customer": [
            {
                "customer_id": r["customer_id"],
                "expected": (r["validation"].get("expected_value") or {}),
                "observed": (r["validation"].get("observed_value") or {}),
                "value_aligned": r["validation"].get("value_aligned"),
            }
            for r in rows
        ],
        "read_only": True,
    }


def build_cohort_retention_report(*, program_session_id: str) -> dict[str, Any]:
    rows = _cohort_customer_metrics(program_session_id)
    retention_rates = [float(r["metrics"].get("retention_rate") or 0) for r in rows]
    continued = sum(1 for r in rows if r["retention"].get("continued_usage"))
    declining = sum(1 for r in rows if r["retention"].get("declining_usage"))
    dormant = sum(1 for r in rows if r["retention"].get("dormant_usage"))
    return {
        "report_id": "cohort-retention-report",
        "program_session_id": program_session_id,
        "retention_rate": _avg(retention_rates),
        "continued_usage_count": continued,
        "declining_usage_count": declining,
        "dormant_usage_count": dormant,
        "repeatable_retention_signals": continued >= max(1, len(rows) // 2) if rows else False,
        "read_only": True,
    }


def build_customer_success_pattern_report(*, program_session_id: str) -> dict[str, Any]:
    outcomes = build_delivery_outcome_registry(program_session_id=program_session_id).get("outcomes") or []
    adoption = build_cohort_adoption_report(program_session_id=program_session_id)
    success_paths = []
    failure_paths = []
    for outcome in outcomes:
        path = {
            "customer_id": outcome.get("customer_id"),
            "request_type": outcome.get("request_type"),
            "scenario_id": outcome.get("scenario_id"),
            "passed": outcome.get("certification_passed"),
        }
        if outcome.get("certification_passed"):
            success_paths.append(path)
        else:
            failure_paths.append(path)

    onboarding_patterns = []
    provider_patterns = []
    for customer in _cohort_entries(program_session_id=program_session_id):
        if customer.get("use_case"):
            onboarding_patterns.append(str(customer.get("use_case")))
        if customer.get("environment"):
            provider_patterns.append(str(customer.get("environment")))

    return {
        "report_id": "customer-success-pattern-report",
        "program_session_id": program_session_id,
        "common_success_paths": success_paths,
        "common_failure_paths": failure_paths,
        "success_pattern_frequency": len(success_paths),
        "onboarding_patterns": sorted(set(onboarding_patterns)),
        "provider_patterns": sorted(set(provider_patterns)),
        "repeatable_satisfaction": adoption.get("repeatable_adoption"),
        "read_only": True,
    }


def build_multi_customer_opportunity_registry(*, program_session_id: str) -> dict[str, Any]:
    value = build_cohort_value_report(program_session_id=program_session_id)
    retention = build_cohort_retention_report(program_session_id=program_session_id)
    opportunities: list[dict[str, Any]] = []
    if value.get("unrealized_count", 0) > 0:
        opportunities.append(
            {
                "opportunity_id": "value-realization-gap",
                "category": "value_realization",
                "detail": "Some cohort members have unrealized value — advisory only",
                "automatic_action_forbidden": True,
            }
        )
    if retention.get("dormant_usage_count", 0) > 0:
        opportunities.append(
            {
                "opportunity_id": "retention-reactivation",
                "category": "adoption",
                "detail": "Dormant usage detected across cohort — no automated outreach",
                "automatic_action_forbidden": True,
            }
        )
    opportunities.append(
        {
            "opportunity_id": "onboarding-education",
            "category": "education",
            "detail": "Document common success paths for repeatable onboarding",
            "automatic_action_forbidden": True,
        }
    )
    return {
        "registry_id": "multi-customer-opportunity-registry",
        "program_session_id": program_session_id,
        "opportunity_count": len(opportunities),
        "opportunities": opportunities,
        "read_only": True,
    }


def compute_proof_metrics(*, program_session_id: str) -> dict[str, Any]:
    adoption = build_cohort_adoption_report(program_session_id=program_session_id)
    value = build_cohort_value_report(program_session_id=program_session_id)
    retention = build_cohort_retention_report(program_session_id=program_session_id)
    patterns = build_customer_success_pattern_report(program_session_id=program_session_id)
    cohort_size = len(_cohort_entries(program_session_id=program_session_id))
    success_count = patterns.get("success_pattern_frequency", 0)
    repeatability = round(success_count / cohort_size, 3) if cohort_size else 0.0
    satisfaction = "positive" if value.get("repeatable_value_realization") else "mixed"
    return {
        "adoption_rate": adoption.get("adoption_rate", 0.0),
        "retention_rate": retention.get("retention_rate", 0.0),
        "value_realization_score": value.get("value_realization_score", 0.0),
        "customer_satisfaction": satisfaction,
        "repeatability_score": repeatability,
        "success_pattern_frequency": success_count,
        "read_only": True,
    }


def register_cohort_customer_from_text(*, program_session_id: str, body: str) -> dict[str, Any]:
    kv = _parse_kv_blob(body)
    customer_id = kv.get("customer_id") or kv.get("customer") or f"customer-{len(_cohort_entries(program_session_id=program_session_id)) + 1}"
    entry = register_cohort_customer(
        entry={
            "customer_id": customer_id,
            "program_session_id": program_session_id,
            "customer_session_id": kv.get("session_id") or kv.get("customer_session_id") or f"{program_session_id}-{customer_id}"[:64],
            "use_case": kv.get("use_case") or kv.get("usecase") or "health_check",
            "delivery_type": kv.get("delivery_type") or kv.get("type") or "health_check_endpoint",
            "environment": kv.get("environment") or kv.get("env") or "staging",
        }
    )
    from aethos_core.workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_store import (
        append_multi_customer_value_proof_record,
    )

    append_multi_customer_value_proof_record(
        session_id=program_session_id,
        kind="multi_customer_cohort_entry",
        content=body,
        metadata=entry,
    )
    return entry
