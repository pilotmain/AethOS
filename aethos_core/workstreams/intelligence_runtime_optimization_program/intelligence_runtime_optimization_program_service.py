# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E2 / FIX 344 — compose intelligence runtime optimization program."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_344_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_contract import (
    AUTHORITY_EXPANSION_FIX_344,
    CORE_PRINCIPLE,
    EXECUTIVE_FIX_MODULES,
    FORBIDDEN_RUNTIME_OPTIMIZATION_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_344,
    GOVERNANCE_MUTATION_PERFORMED_FIX_344,
    INTELLIGENCE_RUNTIME_OPTIMIZATION_PHASES,
    INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_FIX,
    INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_ID,
    INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_INVARIANT,
    INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_SCHEMA_VERSION,
    LOCAL_RUNTIME_OPTIMIZATION_EXECUTABLE_FIX_344,
    MUTATION_PERFORMED_FIX_344,
    PROGRAM_NON_GOALS,
    RUNTIME_OPTIMIZATION_METRICS,
    TRUST_MUTATION_AUTHORITY_FIX_344,
    TRUTH_REDUCTION_FIX_344,
)
from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_executor import (
    build_artifact_persistence_report,
    build_dependency_flattening_report,
    build_memoization_opportunity_report,
    build_runtime_dependency_registry,
    build_runtime_hotspot_registry,
    build_runtime_optimization_opportunity_registry,
    build_runtime_optimization_priority_matrix,
    compute_runtime_metrics,
)
from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_store import (
    has_runtime_optimization_review_approve,
    list_intelligence_runtime_optimization_records,
    list_runtime_metrics_registry_entries,
)


@dataclass(frozen=True)
class IntelligenceRuntimeOptimizationProgramResult:
    ok: bool
    session_id: str
    intelligence_runtime_optimization_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _latest_metrics(*, session_id: str) -> dict[str, Any]:
    rows = _session_records(list_runtime_metrics_registry_entries(), session_id=session_id)
    return rows[-1] if rows else compute_runtime_metrics(session_id=session_id)


def _build_phase_8_executive_visibility(*, session_id: str) -> dict[str, Any]:
    metrics = _latest_metrics(session_id=session_id)
    opportunities = build_runtime_optimization_opportunity_registry(session_id=session_id)
    module_assessments = {
        fix_label: {"runtime_optimization_representable": True, "compose_available": True}
        for fix_label in EXECUTIVE_FIX_MODULES
    }
    return {
        "runtime_optimization_dashboard": {
            "dashboard_id": "runtime-optimization-dashboard",
            "runtime_metrics": metrics,
            "opportunity_count": opportunities.get("opportunity_count"),
            "module_assessments": module_assessments,
            "scalability_improving": float(metrics.get("compose_duration_reduction") or 0.0) > 0,
            "truth_reduction_performed": False,
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, session_id: str) -> dict[str, Any]:
    records = _session_records(list_intelligence_runtime_optimization_records(), session_id=session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "runtime_optimization_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("runtime_optimization_review_")]
    return {
        "runtime_optimization_review_registry": {
            "registry_id": "runtime-optimization-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "human_adoption_required": True,
            "read_only": True,
        }
    }


def _success_criteria(*, session_id: str) -> dict[str, Any]:
    hotspots = build_runtime_hotspot_registry(session_id=session_id)
    flattening = build_dependency_flattening_report(session_id=session_id)
    opportunities = build_runtime_optimization_opportunity_registry(session_id=session_id)
    metrics = _latest_metrics(session_id=session_id)

    return {
        "runtime_hotspots_identified": hotspots.get("hotspot_count", 0) >= 1,
        "dependency_flattening_planned": flattening.get("dependency_depth_reduction", 0) >= 1,
        "optimization_opportunities_registered": opportunities.get("opportunity_count", 0) >= 1,
        "runtime_metrics_tracked": all(key in metrics for key in RUNTIME_OPTIMIZATION_METRICS),
        "compose_duration_reduction_projected": float(metrics.get("compose_duration_reduction") or 0.0) > 0,
        "truth_reduction_performed": False,
        "governance_unchanged": True,
        "program_complete": (
            hotspots.get("hotspot_count", 0) >= 1
            and opportunities.get("opportunity_count", 0) >= 1
            and has_runtime_optimization_review_approve(session_id=session_id)
        ),
    }


def build_intelligence_runtime_optimization_program(
    *, session_id: str = "default"
) -> IntelligenceRuntimeOptimizationProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {}
    phase_builders = (
        lambda session_id=sid: {"runtime_dependency_registry": build_runtime_dependency_registry(session_id=session_id)},
        lambda session_id=sid: {
            "memoization_opportunity_report": build_memoization_opportunity_report(session_id=session_id)
        },
        lambda session_id=sid: {"artifact_persistence_report": build_artifact_persistence_report(session_id=session_id)},
        lambda session_id=sid: {"dependency_flattening_report": build_dependency_flattening_report(session_id=session_id)},
        lambda session_id=sid: {"runtime_hotspot_registry": build_runtime_hotspot_registry(session_id=session_id)},
        lambda session_id=sid: {
            "runtime_optimization_opportunity_registry": build_runtime_optimization_opportunity_registry(
                session_id=session_id
            )
        },
        lambda session_id=sid: {
            "runtime_optimization_priority_matrix": build_runtime_optimization_priority_matrix(session_id=session_id)
        },
        _build_phase_8_executive_visibility,
        _build_phase_9_human_review,
    )
    for phase, builder in zip(INTELLIGENCE_RUNTIME_OPTIMIZATION_PHASES, phase_builders, strict=True):
        sections[phase] = [builder(session_id=sid)]

    success = _success_criteria(session_id=sid)
    metrics = _latest_metrics(session_id=sid)
    if not success.get("runtime_hotspots_identified"):
        blockers.append("runtime_hotspot_analysis_pending")
    if not has_runtime_optimization_review_approve(session_id=sid):
        blockers.append("runtime_optimization_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_SCHEMA_VERSION,
        "workstream_id": INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_ID,
        "fix_id": INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_344,
        "execution_performed": success.get("runtime_hotspots_identified") is True,
        "core_principle": CORE_PRINCIPLE,
        "invariant": INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_RUNTIME_OPTIMIZATION_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(INTELLIGENCE_RUNTIME_OPTIMIZATION_PHASES),
        "truth_reduction": TRUTH_REDUCTION_FIX_344,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_344,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_344,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_344,
        "local_runtime_optimization_executable": LOCAL_RUNTIME_OPTIMIZATION_EXECUTABLE_FIX_344,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_344,
        "runtime_metrics": metrics,
        "runtime_optimization_metrics": list(RUNTIME_OPTIMIZATION_METRICS),
        "success_criteria": success,
        "composed_from_workstream_e1_and_fix_343_findings": True,
        "sections": sections,
        "sources": {
            "workstream_e1_intelligence_performance": True,
            "fix_322_product_market_fit_intelligence": True,
            "fix_323_customer_value_realization_intelligence": True,
            "fix_316_operations": True,
            "fix_324_portfolio": True,
            "fix_329_operating_review": True,
            "fix_330_executive_dashboard": True,
        },
        "fix_344_certification_requirements": list(FIX_344_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Intelligence runtime optimization program complete"
        if success.get("program_complete")
        else "Intelligence runtime optimization composed — analysis and human review pending"
    )
    return IntelligenceRuntimeOptimizationProgramResult(
        ok=True,
        session_id=sid,
        intelligence_runtime_optimization_program=board,
        blockers=blockers,
        detail=detail,
    )
