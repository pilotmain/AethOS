# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E1 / FIX 343 — compose intelligence performance program."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_343_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_contract import (
    AUTHORITY_EXPANSION_FIX_343,
    CORE_PRINCIPLE,
    EXECUTIVE_FIX_MODULES,
    FORBIDDEN_PERFORMANCE_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_343,
    GOVERNANCE_MUTATION_PERFORMED_FIX_343,
    INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_FIX,
    INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_ID,
    INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_INVARIANT,
    INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_SCHEMA_VERSION,
    INTELLIGENCE_PERFORMANCE_PHASES,
    LOCAL_PERFORMANCE_ANALYSIS_EXECUTABLE_FIX_343,
    MUTATION_PERFORMED_FIX_343,
    PROGRAM_NON_GOALS,
    TRUST_MUTATION_AUTHORITY_FIX_343,
    TRUTH_REDUCTION_FIX_343,
)
from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_executor import (
    build_compose_dependency_report,
    build_compose_hotspot_registry,
    build_compose_timing_registry,
    build_evidence_cache_report,
    build_incremental_compose_strategy,
    build_performance_opportunity_registry,
    build_performance_priority_matrix,
    compute_latency_trends,
)
from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_store import (
    has_performance_review_approve,
    list_intelligence_performance_records,
)


@dataclass(frozen=True)
class IntelligencePerformanceEvidenceScalabilityProgramResult:
    ok: bool
    session_id: str
    intelligence_performance_evidence_scalability_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_8_executive_visibility(*, session_id: str) -> dict[str, Any]:
    trends = compute_latency_trends(session_id=session_id)
    opportunities = build_performance_opportunity_registry(session_id=session_id)
    module_assessments = {
        fix_label: {
            "performance_signals_representable": True,
            "compose_available": True,
        }
        for fix_label in EXECUTIVE_FIX_MODULES
    }
    return {
        "intelligence_performance_dashboard": {
            "dashboard_id": "intelligence-performance-dashboard",
            "latency_trends": trends,
            "opportunity_count": opportunities.get("opportunity_count"),
            "module_assessments": module_assessments,
            "scalability_risk": trends.get("scalability_risk"),
            "truth_reduction_performed": False,
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, session_id: str) -> dict[str, Any]:
    records = _session_records(list_intelligence_performance_records(), session_id=session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "performance_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("performance_review_")]
    return {
        "performance_review_registry": {
            "registry_id": "performance-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "human_adoption_required": True,
            "read_only": True,
        }
    }


def _success_criteria(*, session_id: str) -> dict[str, Any]:
    hotspots = build_compose_hotspot_registry(session_id=session_id)
    dependencies = build_compose_dependency_report(session_id=session_id)
    opportunities = build_performance_opportunity_registry(session_id=session_id)
    trends = compute_latency_trends(session_id=session_id)

    return {
        "compose_hotspots_identified": hotspots.get("hotspot_count", 0) >= 1,
        "duplicate_paths_identified": bool(dependencies.get("duplicate_compose_paths")),
        "recursive_fan_in_identified": bool(dependencies.get("recursive_fan_in_chains")),
        "optimization_opportunities_registered": opportunities.get("opportunity_count", 0) >= 1,
        "scalability_risk_assessed": trends.get("scalability_risk") is True,
        "truth_reduction_performed": False,
        "governance_unchanged": True,
        "program_complete": (
            hotspots.get("hotspot_count", 0) >= 1
            and opportunities.get("opportunity_count", 0) >= 1
            and has_performance_review_approve(session_id=session_id)
        ),
    }


def build_intelligence_performance_evidence_scalability_program(
    *, session_id: str = "default"
) -> IntelligencePerformanceEvidenceScalabilityProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {}
    phase_builders = (
        lambda session_id=sid: {"compose_timing_registry": build_compose_timing_registry(session_id=session_id)},
        lambda session_id=sid: {"compose_dependency_report": build_compose_dependency_report(session_id=session_id)},
        lambda session_id=sid: {"evidence_cache_report": build_evidence_cache_report(session_id=session_id)},
        lambda session_id=sid: {"incremental_compose_strategy": build_incremental_compose_strategy(session_id=session_id)},
        lambda session_id=sid: {"compose_hotspot_registry": build_compose_hotspot_registry(session_id=session_id)},
        lambda session_id=sid: {
            "performance_opportunity_registry": build_performance_opportunity_registry(session_id=session_id)
        },
        lambda session_id=sid: {"performance_priority_matrix": build_performance_priority_matrix(session_id=session_id)},
        _build_phase_8_executive_visibility,
        _build_phase_9_human_review,
    )
    for phase, builder in zip(INTELLIGENCE_PERFORMANCE_PHASES, phase_builders, strict=True):
        sections[phase] = [builder(session_id=sid)]

    success = _success_criteria(session_id=sid)
    if not success.get("compose_hotspots_identified"):
        blockers.append("compose_hotspot_analysis_pending")
    if not has_performance_review_approve(session_id=sid):
        blockers.append("performance_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_SCHEMA_VERSION,
        "workstream_id": INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_ID,
        "fix_id": INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_343,
        "execution_performed": success.get("compose_hotspots_identified") is True,
        "core_principle": CORE_PRINCIPLE,
        "invariant": INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_PERFORMANCE_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(INTELLIGENCE_PERFORMANCE_PHASES),
        "truth_reduction": TRUTH_REDUCTION_FIX_343,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_343,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_343,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_343,
        "local_performance_analysis_executable": LOCAL_PERFORMANCE_ANALYSIS_EXECUTABLE_FIX_343,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_343,
        "success_criteria": success,
        "latency_trends": compute_latency_trends(session_id=sid),
        "sections": sections,
        "sources": {
            "fix_322_product_market_fit_intelligence": True,
            "fix_323_customer_value_realization_intelligence": True,
            "fix_319_customer_feedback_intelligence": True,
            "fix_316_operations": True,
            "fix_324_portfolio": True,
            "fix_329_operating_review": True,
            "fix_330_executive_dashboard": True,
        },
        "fix_343_certification_requirements": list(FIX_343_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Intelligence performance program complete"
        if success.get("program_complete")
        else "Intelligence performance composed — analysis and human review pending"
    )
    return IntelligencePerformanceEvidenceScalabilityProgramResult(
        ok=True,
        session_id=sid,
        intelligence_performance_evidence_scalability_program=board,
        blockers=blockers,
        detail=detail,
    )
