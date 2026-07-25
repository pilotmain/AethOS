# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F6 / FIX 352 — unit economics & business sustainability service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_352_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.unit_economics_business_sustainability_program.unit_economics_business_sustainability_program_contract import (
    AUTHORITY_EXPANSION_FIX_352,
    BILLING_EXECUTION_FIX_352,
    COMMERCIAL_AUTHORITY_FIX_352,
    CORE_PRINCIPLE,
    ECONOMIC_COHORT_MIN_SIZE,
    ECONOMIC_METRICS,
    EXECUTIVE_FIX_MODULES,
    FINANCIAL_FORECASTING_AS_FACT_FIX_352,
    FORBIDDEN_ECONOMIC_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_352,
    GOVERNANCE_MUTATION_PERFORMED_FIX_352,
    LOCAL_ECONOMIC_VALIDATION_EXECUTABLE_FIX_352,
    MUTATION_PERFORMED_FIX_352,
    PAYMENT_PROCESSING_FIX_352,
    PLAN_MUTATION_FIX_352,
    PRICING_MUTATION_FIX_352,
    PROGRAM_NON_GOALS,
    TRUST_MUTATION_AUTHORITY_FIX_352,
    UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PHASES,
    UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_FIX,
    UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_ID,
    UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_INVARIANT,
    UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_SCHEMA_VERSION,
)
from aethos_core.workstreams.unit_economics_business_sustainability_program.unit_economics_business_sustainability_program_executor import (
    build_business_sustainability_opportunity_registry,
    build_customer_success_cost_report,
    build_delivery_cost_report,
    build_economic_cohort_registry,
    build_economic_friction_report,
    build_retention_economics_report,
    build_unit_economics_report,
    compute_economic_metrics,
)
from aethos_core.workstreams.unit_economics_business_sustainability_program.unit_economics_business_sustainability_program_store import (
    has_business_sustainability_review_approve,
    list_business_sustainability_records,
)


@dataclass(frozen=True)
class UnitEconomicsBusinessSustainabilityProgramResult:
    ok: bool
    session_id: str
    unit_economics_business_sustainability_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_8_executive_visibility(*, program_session_id: str) -> dict[str, Any]:
    metrics = compute_economic_metrics(program_session_id=program_session_id)
    unit = build_unit_economics_report(program_session_id=program_session_id)
    retention = build_retention_economics_report(program_session_id=program_session_id)
    return {
        "business_sustainability_dashboard": {
            "dashboard_id": "business-sustainability-dashboard",
            "program_session_id": program_session_id,
            "executive_fix_modules": list(EXECUTIVE_FIX_MODULES),
            "fix_305_billing_entitlements": {
                "module": "FIX 305",
                "entitlements_reference_only": True,
                "billing_execution_enabled": False,
            },
            "fix_308_payment_readiness": {
                "module": "FIX 308",
                "readiness_only": True,
                "payment_processing_enabled": False,
            },
            "fix_320_growth_adoption": {
                "module": "FIX 320",
                "retention_strength": metrics.get("retention_strength"),
            },
            "fix_323_value_realization": {
                "module": "FIX 323",
                "estimated_value_delivered_score": unit.get("estimated_value_delivered_score"),
            },
            "fix_330_executive_operating_system": {
                "module": "FIX 330",
                "sustainability_score": metrics.get("sustainability_score"),
            },
            "workstream_f5_commercial_validation_reference": {
                "workstream": "WORKSTREAM_F5",
                "composed_read_only": True,
                "expansion_strength": metrics.get("expansion_strength"),
            },
            "economic_metrics": metrics,
            "financial_forecasting_presented_as_fact": False,
            "commercial_authority_granted": False,
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, program_session_id: str) -> dict[str, Any]:
    records = _session_records(list_business_sustainability_records(), session_id=program_session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "business_sustainability_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("business_sustainability_review_")]
    return {
        "business_sustainability_review_registry": {
            "registry_id": "business-sustainability-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "read_only": True,
        }
    }


def _success_criteria(*, program_session_id: str) -> dict[str, Any]:
    cohort = build_economic_cohort_registry(program_session_id=program_session_id)
    delivery = build_delivery_cost_report(program_session_id=program_session_id)
    success = build_customer_success_cost_report(program_session_id=program_session_id)
    retention = build_retention_economics_report(program_session_id=program_session_id)
    unit = build_unit_economics_report(program_session_id=program_session_id)
    metrics = compute_economic_metrics(program_session_id=program_session_id)
    return {
        "economic_cohort_registered": cohort.get("cohort_size", 0) >= ECONOMIC_COHORT_MIN_SIZE,
        "sustainable_acquisition_signals": delivery.get("delivery_economics_sustainable") is True,
        "sustainable_retention_signals": retention.get("retention_economics_sustainable") is True,
        "sustainable_delivery_economics": delivery.get("delivery_economics_sustainable") is True,
        "sustainable_support_economics": success.get("support_economics_sustainable") is True,
        "sustainable_platform_economics": float(metrics.get("sustainability_score") or 0) >= 0.5,
        "commercial_authority_granted": False,
        "billing_execution_performed": False,
        "financial_forecasting_presented_as_fact": False,
        "program_complete": has_business_sustainability_review_approve(program_session_id=program_session_id),
        "unit_economics_sustainability_score": unit.get("sustainability_score"),
    }


def build_unit_economics_business_sustainability_program(
    *, session_id: str = "default"
) -> UnitEconomicsBusinessSustainabilityProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {
        "phase_1_economic_cohort_registry": [
            {"economic_cohort_registry": build_economic_cohort_registry(program_session_id=sid)}
        ],
        "phase_2_delivery_cost_analysis": [
            {"delivery_cost_report": build_delivery_cost_report(program_session_id=sid)}
        ],
        "phase_3_customer_success_cost_analysis": [
            {"customer_success_cost_report": build_customer_success_cost_report(program_session_id=sid)}
        ],
        "phase_4_retention_economics": [
            {"retention_economics_report": build_retention_economics_report(program_session_id=sid)}
        ],
        "phase_5_unit_economics_analysis": [
            {"unit_economics_report": build_unit_economics_report(program_session_id=sid)}
        ],
        "phase_6_economic_friction_analysis": [
            {"economic_friction_report": build_economic_friction_report(program_session_id=sid)}
        ],
        "phase_7_sustainability_opportunity_registry": [
            {
                "business_sustainability_opportunity_registry": build_business_sustainability_opportunity_registry(
                    program_session_id=sid
                )
            }
        ],
        "phase_8_executive_visibility": [_build_phase_8_executive_visibility(program_session_id=sid)],
        "phase_9_human_review": [_build_phase_9_human_review(program_session_id=sid)],
    }

    success = _success_criteria(program_session_id=sid)
    metrics = compute_economic_metrics(program_session_id=sid)
    cohort_size = build_economic_cohort_registry(program_session_id=sid).get("cohort_size", 0)

    if cohort_size < ECONOMIC_COHORT_MIN_SIZE:
        blockers.append("economic_cohort_minimum_not_met")
    if not has_business_sustainability_review_approve(program_session_id=sid):
        blockers.append("business_sustainability_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_SCHEMA_VERSION,
        "workstream_id": UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_ID,
        "fix_id": UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_352,
        "execution_performed": False,
        "core_principle": CORE_PRINCIPLE,
        "invariant": UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_ECONOMIC_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PHASES),
        "commercial_authority": COMMERCIAL_AUTHORITY_FIX_352,
        "payment_processing": PAYMENT_PROCESSING_FIX_352,
        "billing_execution": BILLING_EXECUTION_FIX_352,
        "pricing_mutation": PRICING_MUTATION_FIX_352,
        "plan_mutation": PLAN_MUTATION_FIX_352,
        "financial_forecasting_as_fact": FINANCIAL_FORECASTING_AS_FACT_FIX_352,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_352,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_352,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_352,
        "local_economic_validation_executable": LOCAL_ECONOMIC_VALIDATION_EXECUTABLE_FIX_352,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_352,
        "economic_cohort_minimum_size": ECONOMIC_COHORT_MIN_SIZE,
        "metrics_tracked": list(ECONOMIC_METRICS),
        "metrics": metrics,
        "success_criteria": success,
        "composed_from_workstreams_f1_through_f5_and_et1_through_et5": True,
        "sections": sections,
        "fix_352_certification_requirements": list(FIX_352_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Unit economics & business sustainability validation complete"
        if success.get("program_complete")
        else "Business sustainability validation composed — human review pending"
    )
    return UnitEconomicsBusinessSustainabilityProgramResult(
        ok=True,
        session_id=sid,
        unit_economics_business_sustainability_program=board,
        blockers=blockers,
        detail=detail,
    )
