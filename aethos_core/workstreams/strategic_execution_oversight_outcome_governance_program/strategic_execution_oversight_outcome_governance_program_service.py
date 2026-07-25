# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_H3 / FIX 360 — strategic execution oversight service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_360_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.strategic_execution_oversight_outcome_governance_program.strategic_execution_oversight_outcome_governance_program_contract import (
    AUTHORITY_EXPANSION_FIX_360,
    AUTOMATIC_INITIATIVE_CHANGES_FIX_360,
    BUDGET_ALLOCATION_FIX_360,
    CORE_PRINCIPLE,
    EXECUTION_AUTHORITY_FIX_360,
    EXECUTIVE_FIX_MODULES,
    FORBIDDEN_OVERSIGHT_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_360,
    GOVERNANCE_BYPASS_FIX_360,
    GOVERNANCE_MUTATION_PERFORMED_FIX_360,
    LOCAL_STRATEGIC_OVERSIGHT_EXECUTABLE_FIX_360,
    MUTATION_PERFORMED_FIX_360,
    OVERSIGHT_INITIATIVE_MIN_SIZE,
    OVERSIGHT_MATURITY_LEVELS,
    OVERSIGHT_METRICS,
    PROGRAM_NON_GOALS,
    RESOURCE_COMMITMENT_FIX_360,
    STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PHASES,
    STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_FIX,
    STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_ID,
    STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_INVARIANT,
    STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_SCHEMA_VERSION,
    STRATEGY_MUTATION_FIX_360,
    TRUST_MUTATION_AUTHORITY_FIX_360,
)
from aethos_core.workstreams.strategic_execution_oversight_outcome_governance_program.strategic_execution_oversight_outcome_governance_program_executor import (
    build_initiative_governance_monitoring_report,
    build_initiative_outcome_report,
    build_initiative_risk_monitoring_report,
    build_outcome_gap_report,
    build_strategic_improvement_registry,
    build_strategic_initiative_oversight_registry,
    build_strategic_learning_report,
    compute_strategic_oversight_metrics,
)
from aethos_core.workstreams.strategic_execution_oversight_outcome_governance_program.strategic_execution_oversight_outcome_governance_program_store import (
    has_strategic_oversight_review_approve,
    list_strategic_oversight_records,
)


@dataclass(frozen=True)
class StrategicExecutionOversightOutcomeGovernanceProgramResult:
    ok: bool
    session_id: str
    strategic_execution_oversight_outcome_governance_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_8_executive_visibility(*, program_session_id: str) -> dict[str, Any]:
    metrics = compute_strategic_oversight_metrics(program_session_id=program_session_id)
    improvements = build_strategic_improvement_registry(program_session_id=program_session_id)
    return {
        "strategic_oversight_dashboard": {
            "dashboard_id": "strategic-oversight-dashboard",
            "program_session_id": program_session_id,
            "executive_fix_modules": list(EXECUTIVE_FIX_MODULES),
            "fix_325_executive_decision_intelligence": {
                "module": "FIX 325",
                "governance_compliance_score": metrics.get("governance_compliance_score"),
                "read_only": True,
            },
            "fix_326_strategic_planning_intelligence": {
                "module": "FIX 326",
                "strategic_learning_score": metrics.get("strategic_learning_score"),
                "read_only": True,
            },
            "fix_330_executive_operating_system": {
                "module": "FIX 330",
                "outcome_realization_score": metrics.get("outcome_realization_score"),
                "execution_authority_granted": False,
            },
            "workstream_h1_strategic_direction_reference": {
                "workstream": "WORKSTREAM_H1",
                "strategic_leverage_score": metrics.get("strategic_leverage_score"),
                "composed_read_only": True,
            },
            "workstream_h2_execution_planning_reference": {
                "workstream": "WORKSTREAM_H2",
                "composed_read_only": True,
            },
            "strategic_oversight_metrics": metrics,
            "oversight_maturity_level": metrics.get("oversight_maturity_level"),
            "open_improvement_count": improvements.get("improvement_count"),
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, program_session_id: str) -> dict[str, Any]:
    records = _session_records(list_strategic_oversight_records(), session_id=program_session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "strategic_oversight_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("strategic_oversight_review_")]
    return {
        "strategic_oversight_review_registry": {
            "registry_id": "strategic-oversight-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "read_only": True,
        }
    }


def _success_criteria(*, program_session_id: str) -> dict[str, Any]:
    registry = build_strategic_initiative_oversight_registry(program_session_id=program_session_id)
    outcomes = build_initiative_outcome_report(program_session_id=program_session_id)
    risk = build_initiative_risk_monitoring_report(program_session_id=program_session_id)
    governance = build_initiative_governance_monitoring_report(program_session_id=program_session_id)
    learning = build_strategic_learning_report(program_session_id=program_session_id)
    metrics = compute_strategic_oversight_metrics(program_session_id=program_session_id)

    return {
        "initiative_monitoring_demonstrated": registry.get("initiative_monitoring_demonstrated") is True,
        "outcome_tracking_demonstrated": outcomes.get("outcome_tracking_demonstrated") is True,
        "milestone_governance_demonstrated": governance.get("milestone_governance_demonstrated") is True,
        "risk_monitoring_demonstrated": risk.get("risk_monitoring_demonstrated") is True,
        "strategic_learning_demonstrated": learning.get("strategic_learning_demonstrated") is True,
        "outcome_realization_demonstrated": float(metrics.get("outcome_realization_score") or 0) >= 0,
        "execution_authority_granted": False,
        "strategy_mutation_performed": False,
        "program_complete": has_strategic_oversight_review_approve(program_session_id=program_session_id),
    }


def build_strategic_execution_oversight_outcome_governance_program(
    *, session_id: str = "default"
) -> StrategicExecutionOversightOutcomeGovernanceProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {
        "phase_1_strategic_initiative_oversight_registry": [
            {"strategic_initiative_oversight_registry": build_strategic_initiative_oversight_registry(program_session_id=sid)}
        ],
        "phase_2_outcome_tracking_analysis": [
            {"initiative_outcome_report": build_initiative_outcome_report(program_session_id=sid)}
        ],
        "phase_3_strategic_risk_monitoring": [
            {"initiative_risk_monitoring_report": build_initiative_risk_monitoring_report(program_session_id=sid)}
        ],
        "phase_4_governance_monitoring": [
            {"initiative_governance_monitoring_report": build_initiative_governance_monitoring_report(program_session_id=sid)}
        ],
        "phase_5_strategic_learning_analysis": [
            {"strategic_learning_report": build_strategic_learning_report(program_session_id=sid)}
        ],
        "phase_6_outcome_gap_analysis": [
            {"outcome_gap_report": build_outcome_gap_report(program_session_id=sid)}
        ],
        "phase_7_strategic_improvement_registry": [
            {"strategic_improvement_registry": build_strategic_improvement_registry(program_session_id=sid)}
        ],
        "phase_8_executive_visibility": [_build_phase_8_executive_visibility(program_session_id=sid)],
        "phase_9_human_review": [_build_phase_9_human_review(program_session_id=sid)],
    }

    success = _success_criteria(program_session_id=sid)
    metrics = compute_strategic_oversight_metrics(program_session_id=sid)
    initiative_count = build_strategic_initiative_oversight_registry(program_session_id=sid).get("initiative_count", 0)

    if initiative_count < OVERSIGHT_INITIATIVE_MIN_SIZE:
        blockers.append("oversight_initiative_minimum_not_met")
    if not has_strategic_oversight_review_approve(program_session_id=sid):
        blockers.append("strategic_oversight_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_SCHEMA_VERSION,
        "workstream_id": STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_ID,
        "fix_id": STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_360,
        "execution_performed": False,
        "core_principle": CORE_PRINCIPLE,
        "invariant": STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_OVERSIGHT_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PHASES),
        "execution_authority": EXECUTION_AUTHORITY_FIX_360,
        "strategy_mutation": STRATEGY_MUTATION_FIX_360,
        "budget_allocation": BUDGET_ALLOCATION_FIX_360,
        "resource_commitment": RESOURCE_COMMITMENT_FIX_360,
        "governance_bypass": GOVERNANCE_BYPASS_FIX_360,
        "automatic_initiative_changes": AUTOMATIC_INITIATIVE_CHANGES_FIX_360,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_360,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_360,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_360,
        "local_strategic_oversight_executable": LOCAL_STRATEGIC_OVERSIGHT_EXECUTABLE_FIX_360,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_360,
        "oversight_initiative_minimum_size": OVERSIGHT_INITIATIVE_MIN_SIZE,
        "oversight_maturity_levels": list(OVERSIGHT_MATURITY_LEVELS),
        "metrics_tracked": list(OVERSIGHT_METRICS),
        "metrics": metrics,
        "success_criteria": success,
        "composed_from_h1_h2_and_fix_309_313_324_325_326_330_patterns": True,
        "sections": sections,
        "fix_360_certification_requirements": list(FIX_360_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Strategic execution oversight & outcome governance complete"
        if success.get("program_complete")
        else "Strategic oversight composed — human review pending"
    )
    return StrategicExecutionOversightOutcomeGovernanceProgramResult(
        ok=True,
        session_id=sid,
        strategic_execution_oversight_outcome_governance_program=board,
        blockers=blockers,
        detail=detail,
    )
