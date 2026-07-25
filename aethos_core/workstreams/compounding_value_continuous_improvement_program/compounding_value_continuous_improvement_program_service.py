# SPDX-License-Identifier: Apache-2.0
"""PHASE_J3 / FIX 366 — compounding value continuous improvement service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_366_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.compounding_value_continuous_improvement_program.compounding_value_continuous_improvement_program_contract import (
    AUTHORITY_EXPANSION_FIX_366,
    AUTOMATIC_POLICY_CHANGES_FIX_366,
    AUTONOMOUS_SELF_MODIFICATION_FIX_366,
    AUTONOMOUS_STRATEGIC_CONTROL_FIX_366,
    COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PHASES,
    COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_FIX,
    COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_ID,
    COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_INVARIANT,
    COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_SCHEMA_VERSION,
    COMPOUNDING_VALUE_METRICS,
    CORE_PRINCIPLE,
    EXECUTIVE_WORKSTREAM_MODULES,
    FORBIDDEN_CONTINUOUS_IMPROVEMENT_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_366,
    GOVERNANCE_BYPASS_FIX_366,
    GOVERNANCE_MUTATION_FIX_366,
    GOVERNANCE_MUTATION_PERFORMED_FIX_366,
    IMPROVEMENT_BASELINE_MIN_SIZE,
    IMPROVEMENT_LEVELS,
    LOCAL_COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_EXECUTABLE_FIX_366,
    MUTATION_PERFORMED_FIX_366,
    PROGRAM_NON_GOALS,
    TRUST_MUTATION_AUTHORITY_FIX_366,
    TRUST_PROMOTION_FIX_366,
)
from aethos_core.workstreams.compounding_value_continuous_improvement_program.compounding_value_continuous_improvement_program_executor import (
    build_business_improvement_report,
    build_continuous_improvement_opportunity_registry,
    build_customer_improvement_report,
    build_delivery_improvement_report,
    build_improvement_baseline_registry,
    build_learning_effectiveness_report,
    build_operational_improvement_report,
    compute_compounding_value_metrics,
)
from aethos_core.workstreams.compounding_value_continuous_improvement_program.compounding_value_continuous_improvement_program_store import (
    has_continuous_improvement_review_approve,
    list_continuous_improvement_records,
)


@dataclass(frozen=True)
class CompoundingValueContinuousImprovementProgramResult:
    ok: bool
    session_id: str
    compounding_value_continuous_improvement_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_8_executive_visibility(*, program_session_id: str) -> dict[str, Any]:
    metrics = compute_compounding_value_metrics(program_session_id=program_session_id)
    opportunities = build_continuous_improvement_opportunity_registry(program_session_id=program_session_id)
    return {
        "compounding_value_dashboard": {
            "dashboard_id": "compounding-value-dashboard",
            "program_session_id": program_session_id,
            "executive_workstream_modules": list(EXECUTIVE_WORKSTREAM_MODULES),
            "phase_j1_production_reality_reference": {
                "phase": "PHASE_J1",
                "composed_read_only": True,
            },
            "phase_j2_comparative_performance_reference": {
                "phase": "PHASE_J2",
                "composed_read_only": True,
            },
            "workstream_h3_oversight_reference": {
                "workstream": "WORKSTREAM_H3",
                "composed_read_only": True,
            },
            "workstream_g4_enterprise_readiness_reference": {
                "workstream": "WORKSTREAM_G4",
                "composed_read_only": True,
            },
            "fix_330_executive_operating_system_dashboard_reference": {
                "fix": "FIX 330",
                "composed_read_only": True,
            },
            "compounding_value_metrics": metrics,
            "improvement_level": metrics.get("improvement_level"),
            "highest_leverage_count": len(opportunities.get("highest_leverage_improvements") or []),
            "self_modification_performed": False,
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, program_session_id: str) -> dict[str, Any]:
    records = _session_records(list_continuous_improvement_records(), session_id=program_session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "continuous_improvement_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("continuous_improvement_review_")]
    return {
        "continuous_improvement_review_registry": {
            "registry_id": "continuous-improvement-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "read_only": True,
        }
    }


def _success_criteria(*, program_session_id: str) -> dict[str, Any]:
    registry = build_improvement_baseline_registry(program_session_id=program_session_id)
    delivery = build_delivery_improvement_report(program_session_id=program_session_id)
    operational = build_operational_improvement_report(program_session_id=program_session_id)
    customer = build_customer_improvement_report(program_session_id=program_session_id)
    business = build_business_improvement_report(program_session_id=program_session_id)
    metrics = compute_compounding_value_metrics(program_session_id=program_session_id)

    return {
        "improvement_baseline_registry_demonstrated": registry.get("baseline_count", 0) >= IMPROVEMENT_BASELINE_MIN_SIZE,
        "improving_delivery_outcomes_demonstrated": delivery.get("delivery_improvement_demonstrated") is True,
        "improving_deployment_outcomes_demonstrated": operational.get("operational_improvement_demonstrated") is True,
        "improving_customer_outcomes_demonstrated": customer.get("customer_improvement_demonstrated") is True,
        "improving_recovery_outcomes_demonstrated": float(operational.get("recovery_improvement") or 0) >= 0,
        "improving_business_outcomes_demonstrated": business.get("business_improvement_demonstrated") is True,
        "compounding_value_signals": float(metrics.get("compounding_value_score") or 0) >= 0.2,
        "self_modification_performed": False,
        "automatic_policy_changes_performed": False,
        "program_complete": has_continuous_improvement_review_approve(program_session_id=program_session_id),
    }


def build_compounding_value_continuous_improvement_program(
    *, session_id: str = "default"
) -> CompoundingValueContinuousImprovementProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {
        "phase_1_improvement_baseline_registry": [
            {"improvement_baseline_registry": build_improvement_baseline_registry(program_session_id=sid)}
        ],
        "phase_2_delivery_improvement_analysis": [
            {"delivery_improvement_report": build_delivery_improvement_report(program_session_id=sid)}
        ],
        "phase_3_operational_improvement_analysis": [
            {"operational_improvement_report": build_operational_improvement_report(program_session_id=sid)}
        ],
        "phase_4_customer_improvement_analysis": [
            {"customer_improvement_report": build_customer_improvement_report(program_session_id=sid)}
        ],
        "phase_5_business_improvement_analysis": [
            {"business_improvement_report": build_business_improvement_report(program_session_id=sid)}
        ],
        "phase_6_learning_effectiveness_analysis": [
            {"learning_effectiveness_report": build_learning_effectiveness_report(program_session_id=sid)}
        ],
        "phase_7_improvement_opportunity_registry": [
            {
                "continuous_improvement_opportunity_registry": build_continuous_improvement_opportunity_registry(
                    program_session_id=sid
                )
            }
        ],
        "phase_8_executive_visibility": [_build_phase_8_executive_visibility(program_session_id=sid)],
        "phase_9_human_review": [_build_phase_9_human_review(program_session_id=sid)],
    }

    success = _success_criteria(program_session_id=sid)
    metrics = compute_compounding_value_metrics(program_session_id=sid)
    baseline_count = build_improvement_baseline_registry(program_session_id=sid).get("baseline_count", 0)

    if baseline_count < IMPROVEMENT_BASELINE_MIN_SIZE:
        blockers.append("improvement_baseline_minimum_not_met")
    if not has_continuous_improvement_review_approve(program_session_id=sid):
        blockers.append("continuous_improvement_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_SCHEMA_VERSION,
        "phase_id": COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_ID,
        "workstream_id": COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_ID,
        "fix_id": COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_366,
        "core_principle": CORE_PRINCIPLE,
        "invariant": COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_CONTINUOUS_IMPROVEMENT_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PHASES),
        "autonomous_self_modification": AUTONOMOUS_SELF_MODIFICATION_FIX_366,
        "automatic_policy_changes": AUTOMATIC_POLICY_CHANGES_FIX_366,
        "autonomous_strategic_control": AUTONOMOUS_STRATEGIC_CONTROL_FIX_366,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_366,
        "governance_mutation": GOVERNANCE_MUTATION_FIX_366,
        "governance_bypass": GOVERNANCE_BYPASS_FIX_366,
        "trust_promotion": TRUST_PROMOTION_FIX_366,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_366,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_366,
        "local_compounding_value_continuous_improvement_executable": LOCAL_COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_EXECUTABLE_FIX_366,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_366,
        "improvement_baseline_minimum_size": IMPROVEMENT_BASELINE_MIN_SIZE,
        "improvement_levels": list(IMPROVEMENT_LEVELS),
        "metrics_tracked": list(COMPOUNDING_VALUE_METRICS),
        "metrics": metrics,
        "success_criteria": success,
        "composed_from_phase_j1_j2_h3_g4_fix330_patterns": True,
        "sections": sections,
        "fix_366_certification_requirements": list(FIX_366_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Compounding value continuous improvement program complete"
        if success.get("program_complete")
        else "Compounding value continuous improvement composed — human review pending"
    )
    return CompoundingValueContinuousImprovementProgramResult(
        ok=True,
        session_id=sid,
        compounding_value_continuous_improvement_program=board,
        blockers=blockers,
        detail=detail,
    )
