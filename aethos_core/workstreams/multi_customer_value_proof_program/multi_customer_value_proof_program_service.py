# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F3 / FIX 349 — multi-customer value proof service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_349_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_contract import (
    AUTHORITY_EXPANSION_FIX_349,
    AUTOMATED_OUTREACH_FIX_349,
    COHORT_MIN_SIZE,
    CORE_PRINCIPLE,
    CUSTOMER_AUTHORITY_FIX_349,
    CUSTOMER_MANIPULATION_FIX_349,
    EXECUTIVE_FIX_MODULES,
    FORBIDDEN_PROOF_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_349,
    GOVERNANCE_MUTATION_PERFORMED_FIX_349,
    LOCAL_MULTI_CUSTOMER_PROOF_EXECUTABLE_FIX_349,
    MULTI_CUSTOMER_VALUE_PROOF_PHASES,
    MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_FIX,
    MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_ID,
    MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_INVARIANT,
    MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_349,
    PROOF_METRICS,
    PROGRAM_NON_GOALS,
    TRUST_MUTATION_AUTHORITY_FIX_349,
)
from aethos_core.workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_executor import (
    build_cohort_adoption_report,
    build_cohort_retention_report,
    build_cohort_value_report,
    build_customer_cohort_registry,
    build_customer_success_pattern_report,
    build_delivery_outcome_registry,
    build_multi_customer_opportunity_registry,
    compute_proof_metrics,
)
from aethos_core.workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_store import (
    has_multi_customer_review_approve,
    list_multi_customer_value_proof_records,
)


@dataclass(frozen=True)
class MultiCustomerValueProofProgramResult:
    ok: bool
    session_id: str
    multi_customer_value_proof_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_8_executive_visibility(*, program_session_id: str) -> dict[str, Any]:
    metrics = compute_proof_metrics(program_session_id=program_session_id)
    adoption = build_cohort_adoption_report(program_session_id=program_session_id)
    value = build_cohort_value_report(program_session_id=program_session_id)
    return {
        "multi_customer_value_dashboard": {
            "dashboard_id": "multi-customer-value-dashboard",
            "program_session_id": program_session_id,
            "executive_fix_modules": list(EXECUTIVE_FIX_MODULES),
            "fix_320_growth_adoption": {
                "module": "FIX 320",
                "cohort_adoption_rate": metrics.get("adoption_rate"),
                "repeatable_adoption": adoption.get("repeatable_adoption"),
            },
            "fix_323_value_realization": {
                "module": "FIX 323",
                "cohort_value_score": metrics.get("value_realization_score"),
                "repeatable_value": value.get("repeatable_value_realization"),
            },
            "fix_330_executive_operating_system": {
                "module": "FIX 330",
                "repeatability_score": metrics.get("repeatability_score"),
            },
            "proof_metrics": metrics,
            "customer_manipulation_performed": False,
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, program_session_id: str) -> dict[str, Any]:
    records = _session_records(list_multi_customer_value_proof_records(), session_id=program_session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "multi_customer_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("multi_customer_review_")]
    return {
        "multi_customer_review_registry": {
            "registry_id": "multi-customer-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "read_only": True,
        }
    }


def _success_criteria(*, program_session_id: str) -> dict[str, Any]:
    cohort = build_customer_cohort_registry(program_session_id=program_session_id)
    adoption = build_cohort_adoption_report(program_session_id=program_session_id)
    value = build_cohort_value_report(program_session_id=program_session_id)
    retention = build_cohort_retention_report(program_session_id=program_session_id)
    patterns = build_customer_success_pattern_report(program_session_id=program_session_id)
    return {
        "multi_customer_cohort_registered": cohort.get("cohort_size", 0) >= COHORT_MIN_SIZE,
        "repeatable_adoption": adoption.get("repeatable_adoption") is True,
        "repeatable_value_realization": value.get("repeatable_value_realization") is True,
        "repeatable_retention_signals": retention.get("repeatable_retention_signals") is True,
        "repeatable_customer_satisfaction": patterns.get("repeatable_satisfaction") is True,
        "customer_authority_granted": False,
        "customer_manipulation_performed": False,
        "program_complete": has_multi_customer_review_approve(program_session_id=program_session_id),
    }


def build_multi_customer_value_proof_program(
    *, session_id: str = "default"
) -> MultiCustomerValueProofProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {
        "phase_1_customer_cohort_registry": [
            {"customer_cohort_registry": build_customer_cohort_registry(program_session_id=sid)}
        ],
        "phase_2_delivery_outcome_registry": [
            {"delivery_outcome_registry": build_delivery_outcome_registry(program_session_id=sid)}
        ],
        "phase_3_adoption_analysis": [{"cohort_adoption_report": build_cohort_adoption_report(program_session_id=sid)}],
        "phase_4_value_analysis": [{"cohort_value_report": build_cohort_value_report(program_session_id=sid)}],
        "phase_5_retention_analysis": [{"cohort_retention_report": build_cohort_retention_report(program_session_id=sid)}],
        "phase_6_success_pattern_discovery": [
            {"customer_success_pattern_report": build_customer_success_pattern_report(program_session_id=sid)}
        ],
        "phase_7_value_opportunity_registry": [
            {"multi_customer_opportunity_registry": build_multi_customer_opportunity_registry(program_session_id=sid)}
        ],
        "phase_8_executive_visibility": [_build_phase_8_executive_visibility(program_session_id=sid)],
        "phase_9_human_review": [_build_phase_9_human_review(program_session_id=sid)],
    }

    success = _success_criteria(program_session_id=sid)
    metrics = compute_proof_metrics(program_session_id=sid)
    cohort_size = build_customer_cohort_registry(program_session_id=sid).get("cohort_size", 0)

    if cohort_size < COHORT_MIN_SIZE:
        blockers.append("customer_cohort_minimum_not_met")
    if not has_multi_customer_review_approve(program_session_id=sid):
        blockers.append("multi_customer_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_SCHEMA_VERSION,
        "workstream_id": MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_ID,
        "fix_id": MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_349,
        "execution_performed": False,
        "core_principle": CORE_PRINCIPLE,
        "invariant": MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_PROOF_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(MULTI_CUSTOMER_VALUE_PROOF_PHASES),
        "customer_authority": CUSTOMER_AUTHORITY_FIX_349,
        "customer_manipulation": CUSTOMER_MANIPULATION_FIX_349,
        "automated_outreach": AUTOMATED_OUTREACH_FIX_349,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_349,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_349,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_349,
        "local_multi_customer_proof_executable": LOCAL_MULTI_CUSTOMER_PROOF_EXECUTABLE_FIX_349,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_349,
        "cohort_minimum_size": COHORT_MIN_SIZE,
        "metrics_tracked": list(PROOF_METRICS),
        "metrics": metrics,
        "success_criteria": success,
        "composed_from_workstream_f1_and_f2": True,
        "sections": sections,
        "fix_349_certification_requirements": list(FIX_349_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Multi-customer value proof complete"
        if success.get("program_complete")
        else "Multi-customer value proof composed — human review pending"
    )
    return MultiCustomerValueProofProgramResult(
        ok=True,
        session_id=sid,
        multi_customer_value_proof_program=board,
        blockers=blockers,
        detail=detail,
    )
