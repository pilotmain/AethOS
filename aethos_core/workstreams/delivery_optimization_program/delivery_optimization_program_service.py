# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_C2 / FIX 340 — compose delivery optimization program."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_340_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.delivery_optimization_program.delivery_optimization_program_contract import (
    AUTONOMOUS_MUTATION_ENABLED_FIX_340,
    AUTHORITY_EXPANSION_FIX_340,
    CORE_PRINCIPLE,
    DELIVERY_AUTHORITY_FIX_340,
    DELIVERY_OPTIMIZATION_PHASES,
    DELIVERY_OPTIMIZATION_PROGRAM_FIX,
    DELIVERY_OPTIMIZATION_PROGRAM_ID,
    DELIVERY_OPTIMIZATION_PROGRAM_INVARIANT,
    DELIVERY_OPTIMIZATION_PROGRAM_SCHEMA_VERSION,
    EXECUTIVE_FIX_MODULES,
    FORBIDDEN_OPTIMIZATION_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_340,
    GOVERNANCE_MUTATION_PERFORMED_FIX_340,
    LOCAL_OPTIMIZATION_ANALYSIS_EXECUTABLE_FIX_340,
    MUTATION_PERFORMED_FIX_340,
    OPTIMIZATION_TREND_METRICS,
    PROGRAM_NON_GOALS,
    PROVIDER_MUTATION_AUTHORITY_FIX_340,
    TRUST_MUTATION_AUTHORITY_FIX_340,
)
from aethos_core.workstreams.delivery_optimization_program.delivery_optimization_program_executor import (
    analyze_failure_intelligence,
    analyze_intervention_intelligence,
    analyze_performance_intelligence,
    analyze_reliability_intelligence,
    build_delivery_outcome_registry,
    build_improvement_opportunity_registry,
    build_optimization_priority_matrix,
    compute_optimization_trends,
)
from aethos_core.workstreams.delivery_optimization_program.delivery_optimization_program_store import (
    has_delivery_optimization_review_approve,
    list_delivery_optimization_records,
)


@dataclass(frozen=True)
class DeliveryOptimizationProgramResult:
    ok: bool
    session_id: str
    delivery_optimization_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_8_executive_visibility(*, session_id: str) -> dict[str, Any]:
    trends = compute_optimization_trends(session_id=session_id)
    opportunities = build_improvement_opportunity_registry(session_id=session_id)
    evidence_present = opportunities.get("opportunity_count", 0) > 0

    module_assessments: dict[str, Any] = {}
    for fix_label in EXECUTIVE_FIX_MODULES:
        module_assessments[fix_label] = {
            "optimization_signals_representable": evidence_present,
            "compose_available": True,
        }

    delivery_optimization_dashboard = {
        "dashboard_id": "delivery-optimization-dashboard",
        "trends": trends,
        "opportunity_count": opportunities.get("opportunity_count"),
        "module_assessments": module_assessments,
        "executive_fix_modules": list(EXECUTIVE_FIX_MODULES),
        "autonomous_mutation": False,
        "read_only": True,
    }
    return {"delivery_optimization_dashboard": delivery_optimization_dashboard}


def _build_phase_9_human_review(*, session_id: str) -> dict[str, Any]:
    records = _session_records(list_delivery_optimization_records(), session_id=session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "delivery_optimization_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("delivery_optimization_review_")]

    delivery_optimization_review_registry = {
        "registry_id": "delivery-optimization-review-registry",
        "note_count": len(notes),
        "decision_count": len(decisions),
        "notes": notes[-10:],
        "decisions": decisions[-5:],
        "human_adoption_required": True,
        "read_only": True,
    }
    return {"delivery_optimization_review_registry": delivery_optimization_review_registry}


def _success_criteria(*, session_id: str) -> dict[str, Any]:
    failures = analyze_failure_intelligence(session_id=session_id)
    interventions = analyze_intervention_intelligence(session_id=session_id)
    performance = analyze_performance_intelligence(session_id=session_id)
    opportunities = build_improvement_opportunity_registry(session_id=session_id)

    return {
        "recurring_failures_identified": bool(failures.get("recurring_failure_tracks")),
        "recurring_interventions_identified": interventions.get("recurring_interventions") is True,
        "delivery_bottlenecks_identified": bool(performance.get("delivery_bottleneck")),
        "deployment_bottlenecks_identified": performance.get("delivery_bottleneck") == "deployment",
        "verification_bottlenecks_identified": analyze_reliability_intelligence(session_id=session_id).get(
            "verification_rate", 1.0
        )
        < 1.0,
        "improvement_recommendations_present": opportunities.get("opportunity_count", 0) > 0,
        "human_review_approved": has_delivery_optimization_review_approve(session_id=session_id),
        "autonomous_mutation_performed": False,
        "program_complete": (
            opportunities.get("opportunity_count", 0) > 0
            and has_delivery_optimization_review_approve(session_id=session_id)
        ),
    }


def build_delivery_optimization_program(*, session_id: str = "default") -> DeliveryOptimizationProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {}
    phase_builders = (
        lambda session_id=sid: {"delivery_outcome_registry": build_delivery_outcome_registry(session_id=session_id)},
        lambda session_id=sid: {
            "delivery_failure_intelligence_report": analyze_failure_intelligence(session_id=session_id)
        },
        lambda session_id=sid: {
            "delivery_intervention_report": analyze_intervention_intelligence(session_id=session_id)
        },
        lambda session_id=sid: {
            "delivery_performance_report": analyze_performance_intelligence(session_id=session_id)
        },
        lambda session_id=sid: {
            "delivery_reliability_intelligence_report": analyze_reliability_intelligence(session_id=session_id)
        },
        lambda session_id=sid: {
            "delivery_improvement_opportunity_registry": build_improvement_opportunity_registry(session_id=session_id)
        },
        lambda session_id=sid: {
            "delivery_optimization_priority_matrix": build_optimization_priority_matrix(session_id=session_id)
        },
        _build_phase_8_executive_visibility,
        _build_phase_9_human_review,
    )
    for phase, builder in zip(DELIVERY_OPTIMIZATION_PHASES, phase_builders, strict=True):
        sections[phase] = [builder(session_id=sid)]

    success = _success_criteria(session_id=sid)
    trends = compute_optimization_trends(session_id=sid)

    if not success.get("improvement_recommendations_present"):
        blockers.append("optimization_analysis_pending")
    if not has_delivery_optimization_review_approve(session_id=sid):
        blockers.append("delivery_optimization_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": DELIVERY_OPTIMIZATION_PROGRAM_SCHEMA_VERSION,
        "workstream_id": DELIVERY_OPTIMIZATION_PROGRAM_ID,
        "fix_id": DELIVERY_OPTIMIZATION_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_340,
        "execution_performed": False,
        "core_principle": CORE_PRINCIPLE,
        "invariant": DELIVERY_OPTIMIZATION_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_OPTIMIZATION_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(DELIVERY_OPTIMIZATION_PHASES),
        "autonomous_mutation_enabled": AUTONOMOUS_MUTATION_ENABLED_FIX_340,
        "delivery_authority": DELIVERY_AUTHORITY_FIX_340,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_340,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_340,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_340,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_340,
        "local_optimization_analysis_executable": LOCAL_OPTIMIZATION_ANALYSIS_EXECUTABLE_FIX_340,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_340,
        "trends_tracked": list(OPTIMIZATION_TREND_METRICS),
        "trends": trends,
        "success_criteria": success,
        "composed_from_workstream_c1_and_execution_tracks": True,
        "sections": sections,
        "sources": {
            "workstream_c1_real_world_delivery_proof": True,
            "execution_track_5_certification": True,
            "fix_316_operations": True,
            "fix_324_portfolio": True,
            "fix_329_operating_review": True,
            "fix_330_executive_dashboard": True,
        },
        "fix_340_certification_requirements": list(FIX_340_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Delivery optimization program complete"
        if success.get("program_complete")
        else "Delivery optimization program composed — analysis and human review pending"
    )
    return DeliveryOptimizationProgramResult(
        ok=True,
        session_id=sid,
        delivery_optimization_program=board,
        blockers=blockers,
        detail=detail,
    )
