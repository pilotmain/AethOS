# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_H2 / FIX 359 — governed strategic execution service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_359_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_contract import (
    AUTHORITY_EXPANSION_FIX_359,
    AUTOMATIC_PRIORITIZATION_FIX_359,
    BUDGET_ALLOCATION_FIX_359,
    CORE_PRINCIPLE,
    EXECUTIVE_FIX_MODULES,
    EXECUTION_AUTHORITY_FIX_359,
    EXECUTION_READINESS_LEVELS,
    FORBIDDEN_EXECUTION_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_359,
    GOVERNANCE_MUTATION_PERFORMED_FIX_359,
    GOVERNED_STRATEGIC_EXECUTION_PHASES,
    GOVERNED_STRATEGIC_EXECUTION_PROGRAM_FIX,
    GOVERNED_STRATEGIC_EXECUTION_PROGRAM_ID,
    GOVERNED_STRATEGIC_EXECUTION_PROGRAM_INVARIANT,
    GOVERNED_STRATEGIC_EXECUTION_PROGRAM_SCHEMA_VERSION,
    INITIATIVE_LAUNCH_FIX_359,
    LOCAL_STRATEGIC_EXECUTION_EXECUTABLE_FIX_359,
    MUTATION_PERFORMED_FIX_359,
    PROGRAM_NON_GOALS,
    PROJECT_CREATION_FIX_359,
    RESOURCE_COMMITMENT_FIX_359,
    ROADMAP_MUTATION_FIX_359,
    STRATEGIC_EXECUTION_AUTHORITY_FIX_359,
    STRATEGIC_EXECUTION_METRICS,
    STRATEGIC_INITIATIVE_MIN_SIZE,
    TRUST_MUTATION_AUTHORITY_FIX_359,
)
from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_executor import (
    build_initiative_decomposition_report,
    build_initiative_dependency_report,
    build_initiative_governance_readiness_report,
    build_initiative_resource_planning_report,
    build_initiative_risk_planning_report,
    build_strategic_execution_opportunity_registry,
    build_strategic_initiative_registry,
    compute_strategic_execution_metrics,
)
from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_store import (
    has_strategic_execution_review_approve,
    list_strategic_execution_records,
)


@dataclass(frozen=True)
class GovernedStrategicExecutionProgramResult:
    ok: bool
    session_id: str
    governed_strategic_execution_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_8_executive_visibility(*, program_session_id: str) -> dict[str, Any]:
    metrics = compute_strategic_execution_metrics(program_session_id=program_session_id)
    opportunities = build_strategic_execution_opportunity_registry(program_session_id=program_session_id)
    return {
        "strategic_execution_dashboard": {
            "dashboard_id": "strategic-execution-dashboard",
            "program_session_id": program_session_id,
            "executive_fix_modules": list(EXECUTIVE_FIX_MODULES),
            "fix_324_strategic_portfolio_intelligence": {
                "module": "FIX 324",
                "strategic_leverage_score": metrics.get("strategic_leverage_score"),
                "read_only": True,
            },
            "fix_325_executive_decision_intelligence": {
                "module": "FIX 325",
                "execution_readiness_score": metrics.get("execution_readiness_score"),
                "read_only": True,
            },
            "fix_326_strategic_planning_intelligence": {
                "module": "FIX 326",
                "initiative_readiness_score": metrics.get("initiative_readiness_score"),
                "read_only": True,
            },
            "fix_330_executive_operating_system": {
                "module": "FIX 330",
                "governance_readiness_score": metrics.get("governance_readiness_score"),
                "execution_authority_granted": False,
            },
            "workstream_h1_strategic_direction_reference": {
                "workstream": "WORKSTREAM_H1",
                "composed_read_only": True,
            },
            "strategic_execution_metrics": metrics,
            "execution_readiness_level": metrics.get("execution_readiness_level"),
            "open_opportunity_count": opportunities.get("opportunity_count"),
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, program_session_id: str) -> dict[str, Any]:
    records = _session_records(list_strategic_execution_records(), session_id=program_session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "strategic_execution_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("strategic_execution_review_")]
    return {
        "strategic_execution_review_registry": {
            "registry_id": "strategic-execution-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "read_only": True,
        }
    }


def _success_criteria(*, program_session_id: str) -> dict[str, Any]:
    registry = build_strategic_initiative_registry(program_session_id=program_session_id)
    decomposition = build_initiative_decomposition_report(program_session_id=program_session_id)
    dependencies = build_initiative_dependency_report(program_session_id=program_session_id)
    governance = build_initiative_governance_readiness_report(program_session_id=program_session_id)
    metrics = compute_strategic_execution_metrics(program_session_id=program_session_id)

    return {
        "strategic_initiative_planning_demonstrated": registry.get("initiative_count", 0) >= STRATEGIC_INITIATIVE_MIN_SIZE,
        "dependency_identification_demonstrated": dependencies.get("dependency_analysis_demonstrated") is True,
        "governance_planning_demonstrated": governance.get("governance_readiness_demonstrated") is True,
        "initiative_decomposition_demonstrated": decomposition.get("initiative_decomposition_demonstrated") is True,
        "execution_readiness_assessed": float(metrics.get("execution_readiness_score") or 0) >= 0.35,
        "measurable_outcomes_defined": registry.get("initiative_count", 0) > 0,
        "execution_authority_granted": False,
        "budget_allocation_performed": False,
        "program_complete": has_strategic_execution_review_approve(program_session_id=program_session_id),
    }


def build_governed_strategic_execution_program(
    *, session_id: str = "default"
) -> GovernedStrategicExecutionProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {
        "phase_1_strategic_initiative_registry": [
            {"strategic_initiative_registry": build_strategic_initiative_registry(program_session_id=sid)}
        ],
        "phase_2_initiative_decomposition": [
            {"initiative_decomposition_report": build_initiative_decomposition_report(program_session_id=sid)}
        ],
        "phase_3_dependency_analysis": [
            {"initiative_dependency_report": build_initiative_dependency_report(program_session_id=sid)}
        ],
        "phase_4_resource_planning_analysis": [
            {"initiative_resource_planning_report": build_initiative_resource_planning_report(program_session_id=sid)}
        ],
        "phase_5_risk_planning_analysis": [
            {"initiative_risk_planning_report": build_initiative_risk_planning_report(program_session_id=sid)}
        ],
        "phase_6_governance_readiness_analysis": [
            {"initiative_governance_readiness_report": build_initiative_governance_readiness_report(program_session_id=sid)}
        ],
        "phase_7_execution_opportunity_registry": [
            {"strategic_execution_opportunity_registry": build_strategic_execution_opportunity_registry(program_session_id=sid)}
        ],
        "phase_8_executive_visibility": [_build_phase_8_executive_visibility(program_session_id=sid)],
        "phase_9_human_review": [_build_phase_9_human_review(program_session_id=sid)],
    }

    success = _success_criteria(program_session_id=sid)
    metrics = compute_strategic_execution_metrics(program_session_id=sid)
    initiative_count = build_strategic_initiative_registry(program_session_id=sid).get("initiative_count", 0)

    if initiative_count < STRATEGIC_INITIATIVE_MIN_SIZE:
        blockers.append("strategic_initiative_minimum_not_met")
    if not has_strategic_execution_review_approve(program_session_id=sid):
        blockers.append("strategic_execution_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": GOVERNED_STRATEGIC_EXECUTION_PROGRAM_SCHEMA_VERSION,
        "workstream_id": GOVERNED_STRATEGIC_EXECUTION_PROGRAM_ID,
        "fix_id": GOVERNED_STRATEGIC_EXECUTION_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_359,
        "execution_performed": False,
        "core_principle": CORE_PRINCIPLE,
        "invariant": GOVERNED_STRATEGIC_EXECUTION_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_EXECUTION_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(GOVERNED_STRATEGIC_EXECUTION_PHASES),
        "strategic_execution_authority": STRATEGIC_EXECUTION_AUTHORITY_FIX_359,
        "execution_authority": EXECUTION_AUTHORITY_FIX_359,
        "budget_allocation": BUDGET_ALLOCATION_FIX_359,
        "project_creation": PROJECT_CREATION_FIX_359,
        "resource_commitment": RESOURCE_COMMITMENT_FIX_359,
        "initiative_launch": INITIATIVE_LAUNCH_FIX_359,
        "roadmap_mutation": ROADMAP_MUTATION_FIX_359,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_359,
        "automatic_prioritization": AUTOMATIC_PRIORITIZATION_FIX_359,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_359,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_359,
        "local_strategic_execution_executable": LOCAL_STRATEGIC_EXECUTION_EXECUTABLE_FIX_359,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_359,
        "strategic_initiative_minimum_size": STRATEGIC_INITIATIVE_MIN_SIZE,
        "execution_readiness_levels": list(EXECUTION_READINESS_LEVELS),
        "metrics_tracked": list(STRATEGIC_EXECUTION_METRICS),
        "metrics": metrics,
        "success_criteria": success,
        "composed_from_h1_and_fix_309_313_324_325_326_330_patterns": True,
        "sections": sections,
        "fix_359_certification_requirements": list(FIX_359_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Governed strategic execution program complete"
        if success.get("program_complete")
        else "Strategic execution planning composed — human review pending"
    )
    return GovernedStrategicExecutionProgramResult(
        ok=True,
        session_id=sid,
        governed_strategic_execution_program=board,
        blockers=blockers,
        detail=detail,
    )
