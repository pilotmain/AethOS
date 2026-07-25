# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_G3 / FIX 356 — revenue density & business viability service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_356_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.revenue_density_business_viability_program.revenue_density_business_viability_program_contract import (
    AUTHORITY_EXPANSION_FIX_356,
    BILLING_EXECUTION_FIX_356,
    COMMERCIAL_AUTHORITY_FIX_356,
    CORE_PRINCIPLE,
    EXECUTIVE_FIX_MODULES,
    FORBIDDEN_REVENUE_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_356,
    GOVERNANCE_MUTATION_PERFORMED_FIX_356,
    LOCAL_REVENUE_DENSITY_EXECUTABLE_FIX_356,
    MUTATION_PERFORMED_FIX_356,
    PAYMENT_PROCESSING_FIX_356,
    PLAN_UPGRADE_FIX_356,
    PRICING_MUTATION_FIX_356,
    PROGRAM_NON_GOALS,
    REVENUE_COHORT_MIN_SIZE,
    REVENUE_DENSITY_BUSINESS_VIABILITY_PHASES,
    REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_FIX,
    REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_ID,
    REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_INVARIANT,
    REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_SCHEMA_VERSION,
    REVENUE_DENSITY_METRICS,
    SUBSCRIPTION_MUTATION_FIX_356,
    TRUST_MUTATION_AUTHORITY_FIX_356,
)
from aethos_core.workstreams.revenue_density_business_viability_program.revenue_density_business_viability_program_executor import (
    build_expansion_potential_report,
    build_plan_utilization_report,
    build_retention_value_report,
    build_revenue_cohort_registry,
    build_revenue_friction_report,
    build_revenue_opportunity_registry,
    build_revenue_signal_report,
    compute_revenue_density_metrics,
)
from aethos_core.workstreams.revenue_density_business_viability_program.revenue_density_business_viability_program_store import (
    has_revenue_density_review_approve,
    list_revenue_density_records,
)


@dataclass(frozen=True)
class RevenueDensityBusinessViabilityProgramResult:
    ok: bool
    session_id: str
    revenue_density_business_viability_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_8_executive_visibility(*, program_session_id: str) -> dict[str, Any]:
    metrics = compute_revenue_density_metrics(program_session_id=program_session_id)
    revenue = build_revenue_signal_report(program_session_id=program_session_id)
    return {
        "business_viability_dashboard": {
            "dashboard_id": "business-viability-dashboard",
            "program_session_id": program_session_id,
            "executive_fix_modules": list(EXECUTIVE_FIX_MODULES),
            "fix_305_billing_entitlements": {
                "module": "FIX 305",
                "plan_utilization_score": metrics.get("plan_utilization_score"),
                "billing_execution_enabled": False,
            },
            "fix_308_payment_readiness": {
                "module": "FIX 308",
                "readiness_only": True,
                "payment_processing_enabled": False,
            },
            "fix_320_growth_adoption": {
                "module": "FIX 320",
                "adoption_strength": metrics.get("adoption_strength"),
            },
            "fix_323_value_realization": {
                "module": "FIX 323",
                "retention_strength": metrics.get("retention_strength"),
            },
            "fix_330_executive_operating_system": {
                "module": "FIX 330",
                "business_viability_score": metrics.get("business_viability_score"),
            },
            "workstream_g1_evidence_maturity_reference": {
                "workstream": "WORKSTREAM_G1",
                "composed_read_only": True,
            },
            "workstream_g2_usage_adoption_reference": {
                "workstream": "WORKSTREAM_G2",
                "composed_read_only": True,
            },
            "revenue_density_metrics": metrics,
            "revenue_maturity_distribution": revenue.get("revenue_maturity_distribution"),
            "commercial_authority_granted": False,
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, program_session_id: str) -> dict[str, Any]:
    records = _session_records(list_revenue_density_records(), session_id=program_session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "revenue_density_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("revenue_density_review_")]
    return {
        "revenue_density_review_registry": {
            "registry_id": "revenue-density-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "read_only": True,
        }
    }


def _success_criteria(*, program_session_id: str) -> dict[str, Any]:
    registry = build_revenue_cohort_registry(program_session_id=program_session_id)
    plan_util = build_plan_utilization_report(program_session_id=program_session_id)
    expansion = build_expansion_potential_report(program_session_id=program_session_id)
    retention = build_retention_value_report(program_session_id=program_session_id)
    revenue = build_revenue_signal_report(program_session_id=program_session_id)
    metrics = compute_revenue_density_metrics(program_session_id=program_session_id)
    return {
        "revenue_cohort_registered": registry.get("cohort_size", 0) >= REVENUE_COHORT_MIN_SIZE,
        "plan_engagement_demonstrated": plan_util.get("plan_engagement_demonstrated") is True,
        "expansion_potential_demonstrated": expansion.get("expansion_potential_demonstrated") is True,
        "retention_strength_demonstrated": retention.get("retention_value_demonstrated") is True,
        "revenue_quality_usage_demonstrated": float(revenue.get("revenue_density_score") or 0) > 0,
        "sustainable_value_signals": float(metrics.get("business_viability_score") or 0) >= 0.5,
        "commercial_authority_granted": False,
        "billing_execution_performed": False,
        "program_complete": has_revenue_density_review_approve(program_session_id=program_session_id),
    }


def build_revenue_density_business_viability_program(
    *, session_id: str = "default"
) -> RevenueDensityBusinessViabilityProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {
        "phase_1_revenue_cohort_registry": [
            {"revenue_cohort_registry": build_revenue_cohort_registry(program_session_id=sid)}
        ],
        "phase_2_plan_utilization_analysis": [
            {"plan_utilization_report": build_plan_utilization_report(program_session_id=sid)}
        ],
        "phase_3_expansion_potential_analysis": [
            {"expansion_potential_report": build_expansion_potential_report(program_session_id=sid)}
        ],
        "phase_4_retention_value_analysis": [
            {"retention_value_report": build_retention_value_report(program_session_id=sid)}
        ],
        "phase_5_revenue_signal_analysis": [
            {"revenue_signal_report": build_revenue_signal_report(program_session_id=sid)}
        ],
        "phase_6_revenue_friction_analysis": [
            {"revenue_friction_report": build_revenue_friction_report(program_session_id=sid)}
        ],
        "phase_7_revenue_opportunity_registry": [
            {"revenue_opportunity_registry": build_revenue_opportunity_registry(program_session_id=sid)}
        ],
        "phase_8_executive_visibility": [_build_phase_8_executive_visibility(program_session_id=sid)],
        "phase_9_human_review": [_build_phase_9_human_review(program_session_id=sid)],
    }

    success = _success_criteria(program_session_id=sid)
    metrics = compute_revenue_density_metrics(program_session_id=sid)
    cohort_size = build_revenue_cohort_registry(program_session_id=sid).get("cohort_size", 0)

    if cohort_size < REVENUE_COHORT_MIN_SIZE:
        blockers.append("revenue_cohort_minimum_not_met")
    if not has_revenue_density_review_approve(program_session_id=sid):
        blockers.append("revenue_density_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_SCHEMA_VERSION,
        "workstream_id": REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_ID,
        "fix_id": REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_356,
        "execution_performed": False,
        "core_principle": CORE_PRINCIPLE,
        "invariant": REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_REVENUE_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(REVENUE_DENSITY_BUSINESS_VIABILITY_PHASES),
        "commercial_authority": COMMERCIAL_AUTHORITY_FIX_356,
        "payment_processing": PAYMENT_PROCESSING_FIX_356,
        "billing_execution": BILLING_EXECUTION_FIX_356,
        "subscription_mutation": SUBSCRIPTION_MUTATION_FIX_356,
        "plan_upgrade": PLAN_UPGRADE_FIX_356,
        "pricing_mutation": PRICING_MUTATION_FIX_356,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_356,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_356,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_356,
        "local_revenue_density_executable": LOCAL_REVENUE_DENSITY_EXECUTABLE_FIX_356,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_356,
        "revenue_cohort_minimum_size": REVENUE_COHORT_MIN_SIZE,
        "metrics_tracked": list(REVENUE_DENSITY_METRICS),
        "metrics": metrics,
        "success_criteria": success,
        "composed_from_f5_f6_g1_g2_and_fix_305_308_patterns": True,
        "sections": sections,
        "fix_356_certification_requirements": list(FIX_356_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Revenue density & business viability validation complete"
        if success.get("program_complete")
        else "Business viability validation composed — human review pending"
    )
    return RevenueDensityBusinessViabilityProgramResult(
        ok=True,
        session_id=sid,
        revenue_density_business_viability_program=board,
        blockers=blockers,
        detail=detail,
    )
