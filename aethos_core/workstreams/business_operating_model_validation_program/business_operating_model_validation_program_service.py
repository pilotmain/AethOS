# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F7 / FIX 353 — business operating model validation service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_353_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.business_operating_model_validation_program.business_operating_model_validation_program_contract import (
    AUTHORITY_EXPANSION_FIX_353,
    BUSINESS_AUTOMATION_FIX_353,
    BUSINESS_OPERATING_MODEL_VALIDATION_PHASES,
    BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_FIX,
    BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_ID,
    BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_INVARIANT,
    BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_SCHEMA_VERSION,
    CORE_PRINCIPLE,
    EXECUTIVE_FIX_MODULES,
    FORBIDDEN_OPERATING_MODEL_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_353,
    GOVERNANCE_MUTATION_FIX_353,
    GOVERNANCE_MUTATION_PERFORMED_FIX_353,
    LOCAL_OPERATING_MODEL_VALIDATION_EXECUTABLE_FIX_353,
    MUTATION_PERFORMED_FIX_353,
    OPERATING_AUTHORITY_FIX_353,
    OPERATING_MODEL_COHORT_MIN_SIZE,
    OPERATING_MODEL_METRICS,
    ORGANIZATIONAL_RESTRUCTURING_FIX_353,
    PRICING_MUTATION_FIX_353,
    PROGRAM_NON_GOALS,
    PROVIDER_MUTATION_FIX_353,
    TRUST_MUTATION_AUTHORITY_FIX_353,
)
from aethos_core.workstreams.business_operating_model_validation_program.business_operating_model_validation_program_executor import (
    build_business_sustainability_analysis,
    build_delivery_sustainability_report,
    build_governance_sustainability_report,
    build_operating_model_opportunity_registry,
    build_operating_model_registry,
    build_provider_sustainability_report,
    build_support_sustainability_report,
    compute_operating_model_metrics,
)
from aethos_core.workstreams.business_operating_model_validation_program.business_operating_model_validation_program_store import (
    has_operating_model_review_approve,
    list_operating_model_records,
)


@dataclass(frozen=True)
class BusinessOperatingModelValidationProgramResult:
    ok: bool
    session_id: str
    business_operating_model_validation_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_8_executive_visibility(*, program_session_id: str) -> dict[str, Any]:
    metrics = compute_operating_model_metrics(program_session_id=program_session_id)
    economic = build_business_sustainability_analysis(program_session_id=program_session_id)
    return {
        "operating_model_dashboard": {
            "dashboard_id": "operating-model-dashboard",
            "program_session_id": program_session_id,
            "executive_fix_modules": list(EXECUTIVE_FIX_MODULES),
            "fix_324_strategic_portfolio": {
                "module": "FIX 324",
                "operating_leverage_score": metrics.get("operating_leverage_score"),
                "read_only": True,
            },
            "fix_325_executive_operating_review": {
                "module": "FIX 325",
                "business_sustainability_score": metrics.get("business_sustainability_score"),
                "read_only": True,
            },
            "fix_329_operational_intelligence": {
                "module": "FIX 329",
                "delivery_efficiency": metrics.get("delivery_efficiency"),
                "read_only": True,
            },
            "fix_330_executive_operating_system": {
                "module": "FIX 330",
                "governance_efficiency": metrics.get("governance_efficiency"),
                "read_only": True,
            },
            "workstream_f5_commercial_validation_reference": {
                "workstream": "WORKSTREAM_F5",
                "composed_read_only": True,
            },
            "workstream_f6_unit_economics_reference": {
                "workstream": "WORKSTREAM_F6",
                "sustainability_score": economic.get("sustainability_score"),
                "composed_read_only": True,
            },
            "operating_model_metrics": metrics,
            "operating_authority_granted": False,
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, program_session_id: str) -> dict[str, Any]:
    records = _session_records(list_operating_model_records(), session_id=program_session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "operating_model_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("operating_model_review_")]
    return {
        "operating_model_review_registry": {
            "registry_id": "operating-model-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "read_only": True,
        }
    }


def _success_criteria(*, program_session_id: str) -> dict[str, Any]:
    registry = build_operating_model_registry(program_session_id=program_session_id)
    delivery = build_delivery_sustainability_report(program_session_id=program_session_id)
    support = build_support_sustainability_report(program_session_id=program_session_id)
    governance = build_governance_sustainability_report(program_session_id=program_session_id)
    provider = build_provider_sustainability_report(program_session_id=program_session_id)
    metrics = compute_operating_model_metrics(program_session_id=program_session_id)
    return {
        "operating_model_cohort_registered": registry.get("cohort_size", 0) >= OPERATING_MODEL_COHORT_MIN_SIZE,
        "sustainable_delivery_capacity": delivery.get("delivery_capacity_sustainable") is True,
        "sustainable_support_capacity": support.get("support_capacity_sustainable") is True,
        "sustainable_governance_capacity": governance.get("governance_capacity_sustainable") is True,
        "sustainable_provider_capacity": provider.get("provider_capacity_sustainable") is True,
        "sustainable_customer_growth": float(metrics.get("business_sustainability_score") or 0) >= 0.5,
        "operating_authority_granted": False,
        "governance_mutation_performed": False,
        "program_complete": has_operating_model_review_approve(program_session_id=program_session_id),
    }


def build_business_operating_model_validation_program(
    *, session_id: str = "default"
) -> BusinessOperatingModelValidationProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {
        "phase_1_operating_model_registry": [
            {"operating_model_registry": build_operating_model_registry(program_session_id=sid)}
        ],
        "phase_2_delivery_sustainability_analysis": [
            {"delivery_sustainability_report": build_delivery_sustainability_report(program_session_id=sid)}
        ],
        "phase_3_support_sustainability_analysis": [
            {"support_sustainability_report": build_support_sustainability_report(program_session_id=sid)}
        ],
        "phase_4_governance_sustainability_analysis": [
            {"governance_sustainability_report": build_governance_sustainability_report(program_session_id=sid)}
        ],
        "phase_5_provider_sustainability_analysis": [
            {"provider_sustainability_report": build_provider_sustainability_report(program_session_id=sid)}
        ],
        "phase_6_economic_sustainability_analysis": [
            {"business_sustainability_analysis": build_business_sustainability_analysis(program_session_id=sid)}
        ],
        "phase_7_operating_model_opportunity_registry": [
            {"operating_model_opportunity_registry": build_operating_model_opportunity_registry(program_session_id=sid)}
        ],
        "phase_8_executive_visibility": [_build_phase_8_executive_visibility(program_session_id=sid)],
        "phase_9_human_review": [_build_phase_9_human_review(program_session_id=sid)],
    }

    success = _success_criteria(program_session_id=sid)
    metrics = compute_operating_model_metrics(program_session_id=sid)
    cohort_size = build_operating_model_registry(program_session_id=sid).get("cohort_size", 0)

    if cohort_size < OPERATING_MODEL_COHORT_MIN_SIZE:
        blockers.append("operating_model_cohort_minimum_not_met")
    if not has_operating_model_review_approve(program_session_id=sid):
        blockers.append("operating_model_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_SCHEMA_VERSION,
        "workstream_id": BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_ID,
        "fix_id": BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_353,
        "execution_performed": False,
        "core_principle": CORE_PRINCIPLE,
        "invariant": BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_OPERATING_MODEL_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(BUSINESS_OPERATING_MODEL_VALIDATION_PHASES),
        "operating_authority": OPERATING_AUTHORITY_FIX_353,
        "governance_mutation": GOVERNANCE_MUTATION_FIX_353,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_353,
        "pricing_mutation": PRICING_MUTATION_FIX_353,
        "provider_mutation": PROVIDER_MUTATION_FIX_353,
        "organizational_restructuring": ORGANIZATIONAL_RESTRUCTURING_FIX_353,
        "business_automation": BUSINESS_AUTOMATION_FIX_353,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_353,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_353,
        "local_operating_model_validation_executable": LOCAL_OPERATING_MODEL_VALIDATION_EXECUTABLE_FIX_353,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_353,
        "operating_model_cohort_minimum_size": OPERATING_MODEL_COHORT_MIN_SIZE,
        "metrics_tracked": list(OPERATING_MODEL_METRICS),
        "metrics": metrics,
        "success_criteria": success,
        "composed_from_workstreams_f1_through_f6_and_fix_modules": True,
        "sections": sections,
        "fix_353_certification_requirements": list(FIX_353_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Business operating model validation complete"
        if success.get("program_complete")
        else "Operating model validation composed — human review pending"
    )
    return BusinessOperatingModelValidationProgramResult(
        ok=True,
        session_id=sid,
        business_operating_model_validation_program=board,
        blockers=blockers,
        detail=detail,
    )
