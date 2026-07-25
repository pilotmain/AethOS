# SPDX-License-Identifier: Apache-2.0
"""PHASE_J2 / FIX 365 — real-world comparative performance service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_365_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_contract import (
    AUTHORITY_EXPANSION_FIX_365,
    BENCHMARK_MIN_SIZE,
    COMPARATIVE_PERFORMANCE_METRICS,
    COMPARISON_LEVELS,
    COMPETITIVE_ACTIONS_FIX_365,
    COMPETITIVE_AUTHORITY_FIX_365,
    CORE_PRINCIPLE,
    EXECUTIVE_WORKSTREAM_MODULES,
    FORBIDDEN_COMPARATIVE_PERFORMANCE_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_365,
    GOVERNANCE_BYPASS_FIX_365,
    GOVERNANCE_MUTATION_FIX_365,
    GOVERNANCE_MUTATION_PERFORMED_FIX_365,
    LOCAL_REAL_WORLD_COMPARATIVE_PERFORMANCE_EXECUTABLE_FIX_365,
    MUTATION_PERFORMED_FIX_365,
    PROGRAM_NON_GOALS,
    REAL_WORLD_COMPARATIVE_PERFORMANCE_PHASES,
    REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_FIX,
    REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_ID,
    REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_INVARIANT,
    REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_SCHEMA_VERSION,
    STRATEGY_MUTATION_FIX_365,
    TRUST_MUTATION_AUTHORITY_FIX_365,
    TRUST_PROMOTION_FIX_365,
)
from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_executor import (
    build_benchmark_registry,
    build_comparative_learning_report,
    build_comparative_opportunity_registry,
    build_customer_outcome_comparison_report,
    build_delivery_comparison_report,
    build_deployment_comparison_report,
    build_operational_comparison_report,
    compute_comparative_performance_metrics,
)
from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_store import (
    has_comparative_performance_review_approve,
    list_comparative_performance_records,
)


@dataclass(frozen=True)
class RealWorldComparativePerformanceProgramResult:
    ok: bool
    session_id: str
    real_world_comparative_performance_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_8_executive_visibility(*, program_session_id: str) -> dict[str, Any]:
    metrics = compute_comparative_performance_metrics(program_session_id=program_session_id)
    learning = build_comparative_learning_report(program_session_id=program_session_id)
    return {
        "comparative_performance_dashboard": {
            "dashboard_id": "comparative-performance-dashboard",
            "program_session_id": program_session_id,
            "executive_workstream_modules": list(EXECUTIVE_WORKSTREAM_MODULES),
            "phase_j1_production_reality_reference": {
                "phase": "PHASE_J1",
                "composed_read_only": True,
            },
            "phase_i3_autonomous_operations_certification_reference": {
                "phase": "PHASE_I3",
                "composed_read_only": True,
            },
            "workstream_g4_enterprise_readiness_reference": {
                "workstream": "WORKSTREAM_G4",
                "composed_read_only": True,
            },
            "workstream_h3_oversight_reference": {
                "workstream": "WORKSTREAM_H3",
                "composed_read_only": True,
            },
            "fix_330_executive_operating_system_dashboard_reference": {
                "fix": "FIX 330",
                "composed_read_only": True,
            },
            "comparative_performance_metrics": metrics,
            "comparison_level": metrics.get("comparison_level"),
            "aethos_performs_better_count": len(learning.get("aethos_performs_better") or []),
            "competitive_authority_granted": False,
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, program_session_id: str) -> dict[str, Any]:
    records = _session_records(list_comparative_performance_records(), session_id=program_session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "comparative_performance_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("comparative_performance_review_")]
    return {
        "comparative_performance_review_registry": {
            "registry_id": "comparative-performance-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "read_only": True,
        }
    }


def _success_criteria(*, program_session_id: str) -> dict[str, Any]:
    registry = build_benchmark_registry(program_session_id=program_session_id)
    delivery = build_delivery_comparison_report(program_session_id=program_session_id)
    deployment = build_deployment_comparison_report(program_session_id=program_session_id)
    customer = build_customer_outcome_comparison_report(program_session_id=program_session_id)
    operational = build_operational_comparison_report(program_session_id=program_session_id)
    metrics = compute_comparative_performance_metrics(program_session_id=program_session_id)

    return {
        "benchmark_registry_demonstrated": registry.get("benchmark_count", 0) >= BENCHMARK_MIN_SIZE,
        "delivery_comparison_demonstrated": delivery.get("delivery_comparison_demonstrated") is True,
        "deployment_comparison_demonstrated": deployment.get("deployment_comparison_demonstrated") is True,
        "customer_outcome_comparison_demonstrated": customer.get("customer_outcome_comparison_demonstrated") is True,
        "operational_comparison_demonstrated": operational.get("operational_comparison_demonstrated") is True,
        "comparative_learning_demonstrated": build_comparative_learning_report(program_session_id=program_session_id).get(
            "comparative_learning_demonstrated"
        )
        is True,
        "comparative_value_signals": any(
            float(metrics.get(key) or 0) != 0 for key in COMPARATIVE_PERFORMANCE_METRICS
        ),
        "competitive_authority_granted": False,
        "strategy_mutation_performed": False,
        "program_complete": has_comparative_performance_review_approve(program_session_id=program_session_id),
    }


def build_real_world_comparative_performance_program(
    *, session_id: str = "default"
) -> RealWorldComparativePerformanceProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {
        "phase_1_benchmark_registry": [{"benchmark_registry": build_benchmark_registry(program_session_id=sid)}],
        "phase_2_delivery_comparison_analysis": [
            {"delivery_comparison_report": build_delivery_comparison_report(program_session_id=sid)}
        ],
        "phase_3_deployment_comparison_analysis": [
            {"deployment_comparison_report": build_deployment_comparison_report(program_session_id=sid)}
        ],
        "phase_4_customer_outcome_comparison": [
            {"customer_outcome_comparison_report": build_customer_outcome_comparison_report(program_session_id=sid)}
        ],
        "phase_5_operational_comparison_analysis": [
            {"operational_comparison_report": build_operational_comparison_report(program_session_id=sid)}
        ],
        "phase_6_comparative_learning_analysis": [
            {"comparative_learning_report": build_comparative_learning_report(program_session_id=sid)}
        ],
        "phase_7_comparative_opportunity_registry": [
            {"comparative_opportunity_registry": build_comparative_opportunity_registry(program_session_id=sid)}
        ],
        "phase_8_executive_visibility": [_build_phase_8_executive_visibility(program_session_id=sid)],
        "phase_9_human_review": [_build_phase_9_human_review(program_session_id=sid)],
    }

    success = _success_criteria(program_session_id=sid)
    metrics = compute_comparative_performance_metrics(program_session_id=sid)
    benchmark_count = build_benchmark_registry(program_session_id=sid).get("benchmark_count", 0)

    if benchmark_count < BENCHMARK_MIN_SIZE:
        blockers.append("benchmark_minimum_not_met")
    if not has_comparative_performance_review_approve(program_session_id=sid):
        blockers.append("comparative_performance_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_SCHEMA_VERSION,
        "phase_id": REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_ID,
        "workstream_id": REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_ID,
        "fix_id": REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_365,
        "core_principle": CORE_PRINCIPLE,
        "invariant": REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_COMPARATIVE_PERFORMANCE_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(REAL_WORLD_COMPARATIVE_PERFORMANCE_PHASES),
        "competitive_authority": COMPETITIVE_AUTHORITY_FIX_365,
        "competitive_actions": COMPETITIVE_ACTIONS_FIX_365,
        "strategy_mutation": STRATEGY_MUTATION_FIX_365,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_365,
        "governance_mutation": GOVERNANCE_MUTATION_FIX_365,
        "governance_bypass": GOVERNANCE_BYPASS_FIX_365,
        "trust_promotion": TRUST_PROMOTION_FIX_365,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_365,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_365,
        "local_real_world_comparative_performance_executable": LOCAL_REAL_WORLD_COMPARATIVE_PERFORMANCE_EXECUTABLE_FIX_365,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_365,
        "benchmark_minimum_size": BENCHMARK_MIN_SIZE,
        "comparison_levels": list(COMPARISON_LEVELS),
        "metrics_tracked": list(COMPARATIVE_PERFORMANCE_METRICS),
        "metrics": metrics,
        "success_criteria": success,
        "composed_from_phase_j1_i3_g4_h3_fix330_patterns": True,
        "sections": sections,
        "fix_365_certification_requirements": list(FIX_365_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Real-world comparative performance program complete"
        if success.get("program_complete")
        else "Real-world comparative performance composed — human review pending"
    )
    return RealWorldComparativePerformanceProgramResult(
        ok=True,
        session_id=sid,
        real_world_comparative_performance_program=board,
        blockers=blockers,
        detail=detail,
    )
