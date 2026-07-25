# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E3 / FIX 345 — compose intelligence scalability implementation program."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_345_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_contract import (
    AUTHORITY_EXPANSION_FIX_345,
    CORE_PRINCIPLE,
    EXECUTIVE_FIX_MODULES,
    FORBIDDEN_SCALABILITY_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_345,
    GOVERNANCE_MUTATION_PERFORMED_FIX_345,
    INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PHASES,
    INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_FIX,
    INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_ID,
    INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_INVARIANT,
    INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_SCHEMA_VERSION,
    LOCAL_SCALABILITY_IMPLEMENTATION_EXECUTABLE_FIX_345,
    MUTATION_PERFORMED_FIX_345,
    EXECUTION_PERFORMED_FIX_345,
    PROGRAM_NON_GOALS,
    SCALABILITY_METRICS,
    TRUST_MUTATION_AUTHORITY_FIX_345,
    TRUTH_MUTATION_FIX_345,
)
from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_executor import (
    build_runtime_benchmark_report,
    build_scalability_opportunity_registry,
    build_truth_preservation_report,
    execute_dependency_flattening,
    implement_memoization,
    implement_pmf_snapshot_persistence,
    implement_value_realization_snapshot,
)
from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_store import (
    has_scalability_review_approve,
    list_implementation_registry_entries,
    list_intelligence_scalability_records,
    list_runtime_benchmark_registry_entries,
)


@dataclass(frozen=True)
class IntelligenceScalabilityImplementationProgramResult:
    ok: bool
    session_id: str
    intelligence_scalability_implementation_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _implementation_rows(*, session_id: str, phase: str) -> list[dict[str, Any]]:
    return [
        row
        for row in list_implementation_registry_entries()
        if str(row.get("session_id") or "") == session_id and str(row.get("phase") or "") == phase
    ]


def _phase_report(
    *,
    session_id: str,
    phase: str,
    report_id: str,
    builder,
    run_if_missing: bool = False,
) -> dict[str, Any]:
    rows = _implementation_rows(session_id=session_id, phase=phase)
    if rows:
        return {report_id: {**rows[-1], "report_id": report_id, "read_only": True}}
    if run_if_missing:
        return {report_id: builder(session_id=session_id)}
    return {
        report_id: {
            "report_id": report_id,
            "phase": phase,
            "implementation_pending": True,
            "read_only": True,
        }
    }


def _benchmark_report(*, session_id: str) -> dict[str, Any]:
    benchmark = _latest_benchmark(session_id=session_id)
    if benchmark:
        return {
            "runtime_benchmark_report": {
                "report_id": "runtime-benchmark-report",
                "benchmark": benchmark,
                "compose_duration_reduction_pct": benchmark.get("compose_duration_reduction_pct"),
                "read_only": True,
            }
        }
    return {
        "runtime_benchmark_report": {
            "report_id": "runtime-benchmark-report",
            "implementation_pending": True,
            "read_only": True,
        }
    }


def _latest_benchmark(*, session_id: str) -> dict[str, Any]:
    rows = _session_records(list_runtime_benchmark_registry_entries(), session_id=session_id)
    return rows[-1] if rows else {}


def _build_phase_8_executive_visibility(*, session_id: str) -> dict[str, Any]:
    benchmark = _latest_benchmark(session_id=session_id)
    opportunities = build_scalability_opportunity_registry(session_id=session_id)
    module_assessments = {
        fix_label: {"scalability_implementation_representable": True, "compose_available": True}
        for fix_label in EXECUTIVE_FIX_MODULES
    }
    return {
        "intelligence_scalability_dashboard": {
            "dashboard_id": "intelligence-scalability-dashboard",
            "benchmark": benchmark,
            "opportunity_count": opportunities.get("opportunity_count"),
            "module_assessments": module_assessments,
            "runtime_improved": float(benchmark.get("compose_duration_reduction_pct") or 0.0) > 0,
            "truth_mutation_performed": False,
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, session_id: str) -> dict[str, Any]:
    records = _session_records(list_intelligence_scalability_records(), session_id=session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "scalability_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("scalability_review_")]
    return {
        "scalability_review_registry": {
            "registry_id": "scalability-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "human_adoption_required": True,
            "read_only": True,
        }
    }


def _success_criteria(*, session_id: str) -> dict[str, Any]:
    implementations = _session_records(list_implementation_registry_entries(), session_id=session_id)
    benchmark = _latest_benchmark(session_id=session_id)
    truth = build_truth_preservation_report(session_id=session_id)

    phases_implemented = {row.get("phase") for row in implementations}
    required_phases = {
        "memoization_implementation",
        "pmf_snapshot_persistence",
        "value_realization_snapshot_persistence",
        "dependency_flattening_execution",
    }

    return {
        "memoization_implemented": "memoization_implementation" in phases_implemented,
        "pmf_snapshot_persisted": "pmf_snapshot_persistence" in phases_implemented,
        "value_snapshot_persisted": "value_realization_snapshot_persistence" in phases_implemented,
        "dependency_flattening_executed": "dependency_flattening_execution" in phases_implemented,
        "runtime_benchmark_recorded": bool(benchmark),
        "truth_preservation_verified": truth.get("truth_mutation_performed") is False,
        "truth_mutation_performed": False,
        "governance_unchanged": True,
        "program_complete": (
            required_phases.issubset(phases_implemented)
            and bool(benchmark)
            and has_scalability_review_approve(session_id=session_id)
        ),
    }


def build_intelligence_scalability_implementation_program(
    *, session_id: str = "default"
) -> IntelligenceScalabilityImplementationProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {}
    phase_builders = (
        lambda session_id=sid: _phase_report(
            session_id=session_id,
            phase="memoization_implementation",
            report_id="memoization_implementation_report",
            builder=implement_memoization,
            run_if_missing=True,
        ),
        lambda session_id=sid: _phase_report(
            session_id=session_id,
            phase="pmf_snapshot_persistence",
            report_id="pmf_snapshot_report",
            builder=implement_pmf_snapshot_persistence,
        ),
        lambda session_id=sid: _phase_report(
            session_id=session_id,
            phase="value_realization_snapshot_persistence",
            report_id="value_realization_snapshot_report",
            builder=implement_value_realization_snapshot,
        ),
        lambda session_id=sid: _phase_report(
            session_id=session_id,
            phase="dependency_flattening_execution",
            report_id="dependency_flattening_execution_report",
            builder=execute_dependency_flattening,
        ),
        lambda session_id=sid: _benchmark_report(session_id=session_id),
        lambda session_id=sid: {"truth_preservation_report": build_truth_preservation_report(session_id=session_id)},
        lambda session_id=sid: {
            "scalability_opportunity_registry": build_scalability_opportunity_registry(session_id=session_id)
        },
        _build_phase_8_executive_visibility,
        _build_phase_9_human_review,
    )
    for phase, builder in zip(INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PHASES, phase_builders, strict=True):
        sections[phase] = [builder(session_id=sid)]

    success = _success_criteria(session_id=sid)
    benchmark = _latest_benchmark(session_id=sid)
    if not success.get("memoization_implemented"):
        blockers.append("scalability_implementation_pending")
    if not has_scalability_review_approve(session_id=sid):
        blockers.append("scalability_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_SCHEMA_VERSION,
        "workstream_id": INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_ID,
        "fix_id": INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_345,
        "execution_performed": EXECUTION_PERFORMED_FIX_345,
        "core_principle": CORE_PRINCIPLE,
        "invariant": INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_SCALABILITY_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PHASES),
        "truth_mutation": TRUTH_MUTATION_FIX_345,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_345,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_345,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_345,
        "local_scalability_implementation_executable": LOCAL_SCALABILITY_IMPLEMENTATION_EXECUTABLE_FIX_345,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_345,
        "scalability_metrics": list(SCALABILITY_METRICS),
        "runtime_benchmark": benchmark,
        "success_criteria": success,
        "composed_from_workstream_e1_e2_and_fix_343_344": True,
        "sections": sections,
        "sources": {
            "workstream_e1_intelligence_performance": True,
            "workstream_e2_runtime_optimization": True,
            "fix_322_product_market_fit_intelligence": True,
            "fix_323_customer_value_realization_intelligence": True,
            "fix_316_operations": True,
            "fix_324_portfolio": True,
            "fix_329_operating_review": True,
            "fix_330_executive_dashboard": True,
        },
        "fix_345_certification_requirements": list(FIX_345_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Intelligence scalability implementation program complete"
        if success.get("program_complete")
        else "Intelligence scalability implementation composed — execution and human review pending"
    )
    return IntelligenceScalabilityImplementationProgramResult(
        ok=True,
        session_id=sid,
        intelligence_scalability_implementation_program=board,
        blockers=blockers,
        detail=detail,
    )
