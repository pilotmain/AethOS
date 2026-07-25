# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F5 / FIX 351 — commercial validation service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_351_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.commercial_validation_program.commercial_validation_program_contract import (
    AUTHORITY_EXPANSION_FIX_351,
    AUTOMATIC_PLAN_DOWNGRADE_FIX_351,
    AUTOMATIC_PLAN_UPGRADE_FIX_351,
    COMMERCIAL_AUTHORITY_FIX_351,
    COMMERCIAL_COHORT_MIN_SIZE,
    COMMERCIAL_METRICS,
    COMMERCIAL_VALIDATION_PHASES,
    COMMERCIAL_VALIDATION_PROGRAM_FIX,
    COMMERCIAL_VALIDATION_PROGRAM_ID,
    COMMERCIAL_VALIDATION_PROGRAM_INVARIANT,
    COMMERCIAL_VALIDATION_PROGRAM_SCHEMA_VERSION,
    CORE_PRINCIPLE,
    EXECUTIVE_FIX_MODULES,
    FORBIDDEN_COMMERCIAL_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_351,
    GOVERNANCE_MUTATION_PERFORMED_FIX_351,
    LOCAL_COMMERCIAL_VALIDATION_EXECUTABLE_FIX_351,
    MUTATION_PERFORMED_FIX_351,
    PAYMENT_PROCESSING_FIX_351,
    PRICING_MUTATION_FIX_351,
    PROGRAM_NON_GOALS,
    TRUST_MUTATION_AUTHORITY_FIX_351,
)
from aethos_core.workstreams.commercial_validation_program.commercial_validation_program_executor import (
    build_adoption_to_plan_report,
    build_commercial_cohort_registry,
    build_commercial_expansion_report,
    build_commercial_friction_report,
    build_commercial_opportunity_registry,
    build_commercial_retention_report,
    build_value_to_revenue_report,
    compute_commercial_metrics,
)
from aethos_core.workstreams.commercial_validation_program.commercial_validation_program_store import (
    has_commercial_validation_review_approve,
    list_commercial_validation_records,
)


@dataclass(frozen=True)
class CommercialValidationProgramResult:
    ok: bool
    session_id: str
    commercial_validation_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_8_executive_visibility(*, program_session_id: str) -> dict[str, Any]:
    metrics = compute_commercial_metrics(program_session_id=program_session_id)
    retention = build_commercial_retention_report(program_session_id=program_session_id)
    value = build_value_to_revenue_report(program_session_id=program_session_id)
    return {
        "commercial_validation_dashboard": {
            "dashboard_id": "commercial-validation-dashboard",
            "program_session_id": program_session_id,
            "executive_fix_modules": list(EXECUTIVE_FIX_MODULES),
            "fix_305_billing_entitlements": {
                "module": "FIX 305",
                "entitlements_reference_only": True,
                "payment_processing_enabled": False,
            },
            "fix_308_payment_readiness": {
                "module": "FIX 308",
                "readiness_only": True,
                "payment_processing_enabled": False,
            },
            "fix_320_growth_adoption": {
                "module": "FIX 320",
                "activation_rate": metrics.get("activation_rate"),
                "plan_adoption": metrics.get("plan_adoption"),
            },
            "fix_323_value_realization": {
                "module": "FIX 323",
                "value_realization_score": metrics.get("value_realization_score"),
            },
            "fix_330_executive_operating_system": {
                "module": "FIX 330",
                "commercial_sustainability_score": metrics.get("commercial_sustainability_score"),
                "retention_by_plan": retention.get("plans"),
            },
            "commercial_metrics": metrics,
            "commercial_plan_alignment_rate": value.get("commercial_plan_alignment_rate"),
            "commercial_authority_granted": False,
            "payment_processing_performed": False,
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, program_session_id: str) -> dict[str, Any]:
    records = _session_records(list_commercial_validation_records(), session_id=program_session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "commercial_validation_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("commercial_validation_review_")]
    return {
        "commercial_validation_review_registry": {
            "registry_id": "commercial-validation-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "read_only": True,
        }
    }


def _success_criteria(*, program_session_id: str) -> dict[str, Any]:
    cohort = build_commercial_cohort_registry(program_session_id=program_session_id)
    adoption = build_adoption_to_plan_report(program_session_id=program_session_id)
    retention = build_commercial_retention_report(program_session_id=program_session_id)
    expansion = build_commercial_expansion_report(program_session_id=program_session_id)
    value = build_value_to_revenue_report(program_session_id=program_session_id)
    metrics = compute_commercial_metrics(program_session_id=program_session_id)
    return {
        "commercial_cohort_registered": cohort.get("cohort_size", 0) >= COMMERCIAL_COHORT_MIN_SIZE,
        "plan_attractiveness_demonstrated": adoption.get("plan_attractiveness_demonstrated") is True,
        "retention_by_plan_demonstrated": retention.get("retention_by_plan_demonstrated") is True,
        "expansion_signals_tracked": expansion.get("expansion_rate", 0) >= 0,
        "value_plan_alignment_demonstrated": float(value.get("commercial_plan_alignment_rate") or 0) >= 0.5,
        "commercial_sustainability_signals": float(metrics.get("commercial_sustainability_score") or 0) >= 0.5,
        "commercial_authority_granted": False,
        "payment_processing_performed": False,
        "program_complete": has_commercial_validation_review_approve(program_session_id=program_session_id),
    }


def build_commercial_validation_program(*, session_id: str = "default") -> CommercialValidationProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {
        "phase_1_commercial_cohort_registry": [
            {"commercial_cohort_registry": build_commercial_cohort_registry(program_session_id=sid)}
        ],
        "phase_2_adoption_to_plan_analysis": [
            {"adoption_to_plan_report": build_adoption_to_plan_report(program_session_id=sid)}
        ],
        "phase_3_retention_analysis": [
            {"commercial_retention_report": build_commercial_retention_report(program_session_id=sid)}
        ],
        "phase_4_expansion_analysis": [
            {"commercial_expansion_report": build_commercial_expansion_report(program_session_id=sid)}
        ],
        "phase_5_value_to_revenue_analysis": [
            {"value_to_revenue_report": build_value_to_revenue_report(program_session_id=sid)}
        ],
        "phase_6_commercial_friction_analysis": [
            {"commercial_friction_report": build_commercial_friction_report(program_session_id=sid)}
        ],
        "phase_7_commercial_opportunity_registry": [
            {"commercial_opportunity_registry": build_commercial_opportunity_registry(program_session_id=sid)}
        ],
        "phase_8_executive_visibility": [_build_phase_8_executive_visibility(program_session_id=sid)],
        "phase_9_human_review": [_build_phase_9_human_review(program_session_id=sid)],
    }

    success = _success_criteria(program_session_id=sid)
    metrics = compute_commercial_metrics(program_session_id=sid)
    cohort_size = build_commercial_cohort_registry(program_session_id=sid).get("cohort_size", 0)

    if cohort_size < COMMERCIAL_COHORT_MIN_SIZE:
        blockers.append("commercial_cohort_minimum_not_met")
    if not has_commercial_validation_review_approve(program_session_id=sid):
        blockers.append("commercial_validation_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": COMMERCIAL_VALIDATION_PROGRAM_SCHEMA_VERSION,
        "workstream_id": COMMERCIAL_VALIDATION_PROGRAM_ID,
        "fix_id": COMMERCIAL_VALIDATION_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_351,
        "execution_performed": False,
        "core_principle": CORE_PRINCIPLE,
        "invariant": COMMERCIAL_VALIDATION_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_COMMERCIAL_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(COMMERCIAL_VALIDATION_PHASES),
        "commercial_authority": COMMERCIAL_AUTHORITY_FIX_351,
        "payment_processing": PAYMENT_PROCESSING_FIX_351,
        "automatic_plan_upgrade": AUTOMATIC_PLAN_UPGRADE_FIX_351,
        "automatic_plan_downgrade": AUTOMATIC_PLAN_DOWNGRADE_FIX_351,
        "pricing_mutation": PRICING_MUTATION_FIX_351,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_351,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_351,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_351,
        "local_commercial_validation_executable": LOCAL_COMMERCIAL_VALIDATION_EXECUTABLE_FIX_351,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_351,
        "commercial_cohort_minimum_size": COMMERCIAL_COHORT_MIN_SIZE,
        "metrics_tracked": list(COMMERCIAL_METRICS),
        "metrics": metrics,
        "success_criteria": success,
        "composed_from_workstream_f1_f2_f4_and_fix_305_308_patterns": True,
        "sections": sections,
        "fix_351_certification_requirements": list(FIX_351_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Commercial validation complete"
        if success.get("program_complete")
        else "Commercial validation composed — human review pending"
    )
    return CommercialValidationProgramResult(
        ok=True,
        session_id=sid,
        commercial_validation_program=board,
        blockers=blockers,
        detail=detail,
    )
