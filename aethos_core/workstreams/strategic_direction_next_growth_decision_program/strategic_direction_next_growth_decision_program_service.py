# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_H1 / FIX 358 — strategic direction & next-growth decision service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_358_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.strategic_direction_next_growth_decision_program.strategic_direction_next_growth_decision_program_contract import (
    AUTHORITY_EXPANSION_FIX_358,
    AUTOMATIC_PRIORITIZATION_FIX_358,
    BUDGET_ALLOCATION_FIX_358,
    CORE_PRINCIPLE,
    EXECUTIVE_FIX_MODULES,
    FORBIDDEN_STRATEGIC_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_358,
    GOVERNANCE_MUTATION_PERFORMED_FIX_358,
    LOCAL_STRATEGIC_DIRECTION_EXECUTABLE_FIX_358,
    MUTATION_PERFORMED_FIX_358,
    PLAN_EXECUTION_FIX_358,
    PROGRAM_NON_GOALS,
    PROJECT_CREATION_FIX_358,
    RESOURCE_COMMITMENT_FIX_358,
    ROADMAP_MUTATION_FIX_358,
    STRATEGIC_AUTHORITY_FIX_358,
    STRATEGIC_DIRECTION_METRICS,
    STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PHASES,
    STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_FIX,
    STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_ID,
    STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_INVARIANT,
    STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_SCHEMA_VERSION,
    STRATEGIC_OUTCOME_CATEGORIES,
    TRUST_MUTATION_AUTHORITY_FIX_358,
)
from aethos_core.workstreams.strategic_direction_next_growth_decision_program.strategic_direction_next_growth_decision_program_executor import (
    build_customer_strategy_report,
    build_growth_path_report,
    build_product_expansion_report,
    build_provider_strategy_report,
    build_strategic_baseline_registry,
    build_strategic_opportunity_registry,
    build_strategic_tradeoff_report,
    compute_strategic_direction_metrics,
)
from aethos_core.workstreams.strategic_direction_next_growth_decision_program.strategic_direction_next_growth_decision_program_store import (
    has_strategic_direction_review_approve,
    list_strategic_direction_records,
)


@dataclass(frozen=True)
class StrategicDirectionNextGrowthDecisionProgramResult:
    ok: bool
    session_id: str
    strategic_direction_next_growth_decision_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_8_executive_visibility(*, program_session_id: str) -> dict[str, Any]:
    metrics = compute_strategic_direction_metrics(program_session_id=program_session_id)
    tradeoffs = build_strategic_tradeoff_report(program_session_id=program_session_id)
    baselines = build_strategic_baseline_registry(program_session_id=program_session_id)
    return {
        "strategic_direction_dashboard": {
            "dashboard_id": "strategic-direction-dashboard",
            "program_session_id": program_session_id,
            "executive_fix_modules": list(EXECUTIVE_FIX_MODULES),
            "fix_324_strategic_portfolio_intelligence": {
                "module": "FIX 324",
                "strategic_leverage_score": metrics.get("strategic_leverage_score"),
                "read_only": True,
            },
            "fix_325_executive_decision_intelligence": {
                "module": "FIX 325",
                "confidence_score": metrics.get("confidence_score"),
                "read_only": True,
            },
            "fix_326_strategic_planning_intelligence": {
                "module": "FIX 326",
                "growth_potential_score": metrics.get("growth_potential_score"),
                "read_only": True,
            },
            "fix_330_executive_operating_system": {
                "module": "FIX 330",
                "opportunity_score": metrics.get("opportunity_score"),
                "strategic_authority_granted": False,
            },
            "workstream_g4_readiness_reference": {
                "workstream": "WORKSTREAM_G4",
                "readiness_maturity": baselines.get("g4_readiness_maturity"),
                "composed_read_only": True,
            },
            "strategic_direction_metrics": metrics,
            "leading_outcome_category": metrics.get("leading_outcome_category"),
            "strategic_outcome_categories": list(STRATEGIC_OUTCOME_CATEGORIES),
            "tradeoff_summary": tradeoffs.get("tradeoffs", [])[:4],
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, program_session_id: str) -> dict[str, Any]:
    records = _session_records(list_strategic_direction_records(), session_id=program_session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "strategic_direction_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("strategic_direction_review_")]
    return {
        "strategic_direction_review_registry": {
            "registry_id": "strategic-direction-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "read_only": True,
        }
    }


def _success_criteria(*, program_session_id: str) -> dict[str, Any]:
    baseline = build_strategic_baseline_registry(program_session_id=program_session_id)
    growth = build_growth_path_report(program_session_id=program_session_id)
    product = build_product_expansion_report(program_session_id=program_session_id)
    provider = build_provider_strategy_report(program_session_id=program_session_id)
    customer = build_customer_strategy_report(program_session_id=program_session_id)
    tradeoffs = build_strategic_tradeoff_report(program_session_id=program_session_id)
    metrics = compute_strategic_direction_metrics(program_session_id=program_session_id)

    g1_score = float((baseline.get("g1_evidence_maturity") or {}).get("evidence_density_score") or 0)
    g4_score = float((baseline.get("g4_readiness_maturity") or {}).get("overall_platform_maturity_score") or 0)

    return {
        "strategic_baseline_composed": all(
            key in baseline
            for key in (
                "g1_evidence_maturity",
                "g2_adoption_maturity",
                "g3_viability_maturity",
                "g4_readiness_maturity",
            )
        ),
        "growth_opportunities_evaluated": growth.get("growth_opportunities_evaluated") is True,
        "product_expansion_evaluated": product.get("product_expansion_evaluated") is True,
        "provider_strategy_evaluated": provider.get("provider_strategy_evaluated") is True,
        "customer_strategy_evaluated": customer.get("customer_strategy_evaluated") is True,
        "strategic_tradeoffs_analyzed": tradeoffs.get("strategic_tradeoffs_analyzed") is True,
        "strategic_options_scored": float(metrics.get("opportunity_score") or 0) >= 0,
        "evidence_backed_confidence": g1_score > 0 or g4_score > 0,
        "strategic_authority_granted": False,
        "budget_allocation_performed": False,
        "program_complete": has_strategic_direction_review_approve(program_session_id=program_session_id),
    }


def build_strategic_direction_next_growth_decision_program(
    *, session_id: str = "default"
) -> StrategicDirectionNextGrowthDecisionProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {
        "phase_1_strategic_baseline_registry": [
            {"strategic_baseline_registry": build_strategic_baseline_registry(program_session_id=sid)}
        ],
        "phase_2_growth_path_analysis": [
            {"growth_path_report": build_growth_path_report(program_session_id=sid)}
        ],
        "phase_3_product_expansion_analysis": [
            {"product_expansion_report": build_product_expansion_report(program_session_id=sid)}
        ],
        "phase_4_provider_strategy_analysis": [
            {"provider_strategy_report": build_provider_strategy_report(program_session_id=sid)}
        ],
        "phase_5_customer_strategy_analysis": [
            {"customer_strategy_report": build_customer_strategy_report(program_session_id=sid)}
        ],
        "phase_6_strategic_tradeoff_analysis": [
            {"strategic_tradeoff_report": build_strategic_tradeoff_report(program_session_id=sid)}
        ],
        "phase_7_strategic_opportunity_registry": [
            {"strategic_opportunity_registry": build_strategic_opportunity_registry(program_session_id=sid)}
        ],
        "phase_8_executive_visibility": [_build_phase_8_executive_visibility(program_session_id=sid)],
        "phase_9_human_review": [_build_phase_9_human_review(program_session_id=sid)],
    }

    success = _success_criteria(program_session_id=sid)
    metrics = compute_strategic_direction_metrics(program_session_id=sid)

    if not success.get("strategic_baseline_composed"):
        blockers.append("strategic_baseline_incomplete")
    if not has_strategic_direction_review_approve(program_session_id=sid):
        blockers.append("strategic_direction_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_SCHEMA_VERSION,
        "workstream_id": STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_ID,
        "fix_id": STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_358,
        "execution_performed": False,
        "core_principle": CORE_PRINCIPLE,
        "invariant": STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_STRATEGIC_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PHASES),
        "strategic_authority": STRATEGIC_AUTHORITY_FIX_358,
        "budget_allocation": BUDGET_ALLOCATION_FIX_358,
        "project_creation": PROJECT_CREATION_FIX_358,
        "resource_commitment": RESOURCE_COMMITMENT_FIX_358,
        "plan_execution": PLAN_EXECUTION_FIX_358,
        "roadmap_mutation": ROADMAP_MUTATION_FIX_358,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_358,
        "automatic_prioritization": AUTOMATIC_PRIORITIZATION_FIX_358,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_358,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_358,
        "local_strategic_direction_executable": LOCAL_STRATEGIC_DIRECTION_EXECUTABLE_FIX_358,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_358,
        "strategic_outcome_categories": list(STRATEGIC_OUTCOME_CATEGORIES),
        "metrics_tracked": list(STRATEGIC_DIRECTION_METRICS),
        "metrics": metrics,
        "success_criteria": success,
        "composed_from_g1_g2_g3_g4_and_fix_324_325_326_330_patterns": True,
        "sections": sections,
        "fix_358_certification_requirements": list(FIX_358_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Strategic direction & next-growth decision program complete"
        if success.get("program_complete")
        else "Strategic direction composed — human review pending"
    )
    return StrategicDirectionNextGrowthDecisionProgramResult(
        ok=True,
        session_id=sid,
        strategic_direction_next_growth_decision_program=board,
        blockers=blockers,
        detail=detail,
    )
