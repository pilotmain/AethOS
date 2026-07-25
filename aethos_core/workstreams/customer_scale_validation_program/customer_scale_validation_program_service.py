# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F4 / FIX 350 — customer scale validation service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_350_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_contract import (
    AUTHORITY_EXPANSION_FIX_350,
    AUTOMATED_OUTREACH_FIX_350,
    CORE_PRINCIPLE,
    CUSTOMER_AUTHORITY_FIX_350,
    CUSTOMER_MANIPULATION_FIX_350,
    CUSTOMER_SCALE_VALIDATION_PHASES,
    CUSTOMER_SCALE_VALIDATION_PROGRAM_FIX,
    CUSTOMER_SCALE_VALIDATION_PROGRAM_ID,
    CUSTOMER_SCALE_VALIDATION_PROGRAM_INVARIANT,
    CUSTOMER_SCALE_VALIDATION_PROGRAM_SCHEMA_VERSION,
    EXECUTIVE_FIX_MODULES,
    FORBIDDEN_SCALE_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_350,
    GOVERNANCE_MUTATION_PERFORMED_FIX_350,
    LOCAL_SCALE_VALIDATION_EXECUTABLE_FIX_350,
    MUTATION_PERFORMED_FIX_350,
    PROGRAM_NON_GOALS,
    SCALE_COHORT_MIN_SIZE,
    SCALE_METRICS,
    TRUST_MUTATION_AUTHORITY_FIX_350,
)
from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_executor import (
    build_concurrent_delivery_report,
    build_customer_outcome_stability_report,
    build_customer_scale_cohort_registry,
    build_execution_capacity_report,
    build_governance_capacity_report,
    build_provider_capacity_report,
    build_scale_bottleneck_registry,
    compute_scale_metrics,
)
from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_store import (
    has_customer_scale_review_approve,
    list_customer_scale_validation_records,
)


@dataclass(frozen=True)
class CustomerScaleValidationProgramResult:
    ok: bool
    session_id: str
    customer_scale_validation_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_8_executive_visibility(*, program_session_id: str) -> dict[str, Any]:
    metrics = compute_scale_metrics(program_session_id=program_session_id)
    outcomes = build_customer_outcome_stability_report(program_session_id=program_session_id)
    return {
        "customer_scale_dashboard": {
            "dashboard_id": "customer-scale-dashboard",
            "program_session_id": program_session_id,
            "executive_fix_modules": list(EXECUTIVE_FIX_MODULES),
            "fix_320_growth_adoption": {
                "module": "FIX 320",
                "adoption_rate_under_scale": metrics.get("adoption_rate"),
            },
            "fix_323_value_realization": {
                "module": "FIX 323",
                "value_score_under_scale": metrics.get("value_realization_score"),
            },
            "fix_329_operational_intelligence": {
                "module": "FIX 329",
                "concurrent_customers": metrics.get("concurrent_customers"),
            },
            "fix_330_executive_operating_system": {
                "module": "FIX 330",
                "outcomes_stable": outcomes.get("outcomes_stable_under_scale"),
            },
            "scale_metrics": metrics,
            "customer_authority_granted": False,
            "governance_bypass_performed": False,
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, program_session_id: str) -> dict[str, Any]:
    records = _session_records(list_customer_scale_validation_records(), session_id=program_session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "customer_scale_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("customer_scale_review_")]
    return {
        "customer_scale_review_registry": {
            "registry_id": "customer-scale-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "read_only": True,
        }
    }


def _success_criteria(*, program_session_id: str) -> dict[str, Any]:
    delivery = build_concurrent_delivery_report(program_session_id=program_session_id)
    governance = build_governance_capacity_report(program_session_id=program_session_id)
    execution = build_execution_capacity_report(program_session_id=program_session_id)
    outcomes = build_customer_outcome_stability_report(program_session_id=program_session_id)
    cohort = build_customer_scale_cohort_registry(program_session_id=program_session_id)
    return {
        "scale_cohort_registered": cohort.get("cohort_size", 0) >= SCALE_COHORT_MIN_SIZE,
        "concurrent_delivery_demonstrated": delivery.get("simultaneous_delivery_activity", 0) >= SCALE_COHORT_MIN_SIZE,
        "execution_quality_stable": execution.get("execution_quality_stable") is True,
        "governance_workflows_stable": governance.get("governance_bypass_performed") is False,
        "deployment_workflows_stable": execution.get("deployment_throughput", 0) > 0,
        "customer_outcomes_preserved": outcomes.get("outcomes_stable_under_scale") is True,
        "customer_authority_granted": False,
        "program_complete": has_customer_scale_review_approve(program_session_id=program_session_id),
    }


def build_customer_scale_validation_program(
    *, session_id: str = "default"
) -> CustomerScaleValidationProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {
        "phase_1_scale_cohort_registry": [
            {"customer_scale_cohort_registry": build_customer_scale_cohort_registry(program_session_id=sid)}
        ],
        "phase_2_concurrent_delivery_analysis": [
            {"concurrent_delivery_report": build_concurrent_delivery_report(program_session_id=sid)}
        ],
        "phase_3_governance_capacity_analysis": [
            {"governance_capacity_report": build_governance_capacity_report(program_session_id=sid)}
        ],
        "phase_4_execution_capacity_analysis": [
            {"execution_capacity_report": build_execution_capacity_report(program_session_id=sid)}
        ],
        "phase_5_provider_capacity_analysis": [
            {"provider_capacity_report": build_provider_capacity_report(program_session_id=sid)}
        ],
        "phase_6_customer_outcome_stability": [
            {"customer_outcome_stability_report": build_customer_outcome_stability_report(program_session_id=sid)}
        ],
        "phase_7_scale_bottleneck_registry": [
            {"scale_bottleneck_registry": build_scale_bottleneck_registry(program_session_id=sid)}
        ],
        "phase_8_executive_visibility": [_build_phase_8_executive_visibility(program_session_id=sid)],
        "phase_9_human_review": [_build_phase_9_human_review(program_session_id=sid)],
    }

    success = _success_criteria(program_session_id=sid)
    metrics = compute_scale_metrics(program_session_id=sid)
    cohort_size = build_customer_scale_cohort_registry(program_session_id=sid).get("cohort_size", 0)

    if cohort_size < SCALE_COHORT_MIN_SIZE:
        blockers.append("scale_cohort_minimum_not_met")
    if not has_customer_scale_review_approve(program_session_id=sid):
        blockers.append("customer_scale_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": CUSTOMER_SCALE_VALIDATION_PROGRAM_SCHEMA_VERSION,
        "workstream_id": CUSTOMER_SCALE_VALIDATION_PROGRAM_ID,
        "fix_id": CUSTOMER_SCALE_VALIDATION_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_350,
        "execution_performed": False,
        "core_principle": CORE_PRINCIPLE,
        "invariant": CUSTOMER_SCALE_VALIDATION_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_SCALE_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(CUSTOMER_SCALE_VALIDATION_PHASES),
        "customer_authority": CUSTOMER_AUTHORITY_FIX_350,
        "customer_manipulation": CUSTOMER_MANIPULATION_FIX_350,
        "automated_outreach": AUTOMATED_OUTREACH_FIX_350,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_350,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_350,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_350,
        "local_scale_validation_executable": LOCAL_SCALE_VALIDATION_EXECUTABLE_FIX_350,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_350,
        "scale_cohort_minimum_size": SCALE_COHORT_MIN_SIZE,
        "metrics_tracked": list(SCALE_METRICS),
        "metrics": metrics,
        "success_criteria": success,
        "composed_from_workstream_f1_f2_f3_and_d2_patterns": True,
        "sections": sections,
        "fix_350_certification_requirements": list(FIX_350_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Customer scale validation complete"
        if success.get("program_complete")
        else "Customer scale validation composed — human review pending"
    )
    return CustomerScaleValidationProgramResult(
        ok=True,
        session_id=sid,
        customer_scale_validation_program=board,
        blockers=blockers,
        detail=detail,
    )
