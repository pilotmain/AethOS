# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F2 / FIX 348 — customer value & adoption validation service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_348_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_contract import (
    AUTHORITY_EXPANSION_FIX_348,
    AUTOMATED_OUTREACH_FIX_348,
    CORE_PRINCIPLE,
    CUSTOMER_MANIPULATION_FIX_348,
    CUSTOMER_VALUE_ADOPTION_VALIDATION_PHASES,
    CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_FIX,
    CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_ID,
    CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_INVARIANT,
    CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_SCHEMA_VERSION,
    EXECUTIVE_FIX_MODULES,
    FORBIDDEN_VALIDATION_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_348,
    GOVERNANCE_MUTATION_PERFORMED_FIX_348,
    LOCAL_VALUE_VALIDATION_EXECUTABLE_FIX_348,
    MUTATION_PERFORMED_FIX_348,
    PROGRAM_NON_GOALS,
    TRUST_MUTATION_AUTHORITY_FIX_348,
    VALIDATION_METRICS,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_executor import (
    build_customer_adoption_report,
    build_customer_friction_report,
    build_customer_retention_report,
    build_customer_usage_report,
    build_customer_value_opportunity_registry,
    build_customer_value_validation_report,
    build_delivered_solution_registry,
    compute_validation_metrics,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_store import (
    has_customer_value_review_approve,
    list_customer_value_adoption_validation_records,
)


@dataclass(frozen=True)
class CustomerValueAdoptionValidationProgramResult:
    ok: bool
    session_id: str
    customer_value_adoption_validation_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_8_executive_visibility(*, session_id: str) -> dict[str, Any]:
    metrics = compute_validation_metrics(session_id=session_id)
    adoption = build_customer_adoption_report(session_id=session_id)
    validation = build_customer_value_validation_report(session_id=session_id)
    return {
        "customer_value_dashboard": {
            "dashboard_id": "customer-value-dashboard",
            "session_id": session_id,
            "executive_fix_modules": list(EXECUTIVE_FIX_MODULES),
            "fix_310_customer_success": {
                "module": "FIX 310",
                "composed_read_only": True,
                "focus": "customer_health_and_success_signals",
            },
            "fix_320_growth_adoption": {
                "module": "FIX 320",
                "composed_read_only": True,
                "adoption_rate": metrics.get("adoption_rate"),
            },
            "fix_323_value_realization": {
                "module": "FIX 323",
                "composed_read_only": True,
                "value_realization_score": validation.get("value_realization_score"),
            },
            "fix_330_executive_operating_system": {
                "module": "FIX 330",
                "composed_read_only": True,
                "customer_value_panel": {
                    "adoption": adoption.get("active_usage"),
                    "retention_rate": metrics.get("retention_rate"),
                },
            },
            "validation_metrics": metrics,
            "customer_manipulation_performed": False,
            "automated_outreach_performed": False,
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, session_id: str) -> dict[str, Any]:
    records = _session_records(list_customer_value_adoption_validation_records(), session_id=session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "customer_value_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("customer_value_review_")]
    return {
        "customer_value_review_registry": {
            "registry_id": "customer-value-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "read_only": True,
        }
    }


def _success_criteria(*, session_id: str) -> dict[str, Any]:
    registry = build_delivered_solution_registry(session_id=session_id)
    adoption = build_customer_adoption_report(session_id=session_id)
    validation = build_customer_value_validation_report(session_id=session_id)
    retention = build_customer_retention_report(session_id=session_id)
    usage = build_customer_usage_report(session_id=session_id)
    return {
        "delivered_solutions_tracked": registry.get("solution_count", 0) > 0,
        "customer_adoption_evidence": adoption.get("first_use") is True,
        "customer_usage_evidence": usage.get("observation_count", 0) > 0 or usage.get("usage_note_count", 0) > 0,
        "value_realization_evidence": validation.get("value_aligned") is True,
        "retention_signals_present": retention.get("continued_usage") is True or retention.get("retention_rate", 0) > 0,
        "repeat_usage_evidence": adoption.get("repeat_use") is True,
        "customer_manipulation_performed": False,
        "automated_outreach_performed": False,
        "program_complete": has_customer_value_review_approve(session_id=session_id),
    }


def build_customer_value_adoption_validation_program(
    *, session_id: str = "default"
) -> CustomerValueAdoptionValidationProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {
        "phase_1_delivered_solution_registry": [
            {"delivered_solution_registry": build_delivered_solution_registry(session_id=sid)}
        ],
        "phase_2_usage_observation": [{"customer_usage_report": build_customer_usage_report(session_id=sid)}],
        "phase_3_adoption_analysis": [{"customer_adoption_report": build_customer_adoption_report(session_id=sid)}],
        "phase_4_value_validation": [
            {"customer_value_validation_report": build_customer_value_validation_report(session_id=sid)}
        ],
        "phase_5_retention_intelligence": [{"customer_retention_report": build_customer_retention_report(session_id=sid)}],
        "phase_6_friction_analysis": [{"customer_friction_report": build_customer_friction_report(session_id=sid)}],
        "phase_7_opportunity_registry": [
            {"customer_value_opportunity_registry": build_customer_value_opportunity_registry(session_id=sid)}
        ],
        "phase_8_executive_visibility": [_build_phase_8_executive_visibility(session_id=sid)],
        "phase_9_human_review": [_build_phase_9_human_review(session_id=sid)],
    }

    success = _success_criteria(session_id=sid)
    metrics = compute_validation_metrics(session_id=sid)

    if not success.get("delivered_solutions_tracked"):
        blockers.append("delivered_solution_registry_empty")
    if not has_customer_value_review_approve(session_id=sid):
        blockers.append("customer_value_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_SCHEMA_VERSION,
        "workstream_id": CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_ID,
        "fix_id": CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_348,
        "execution_performed": False,
        "core_principle": CORE_PRINCIPLE,
        "invariant": CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_VALIDATION_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(CUSTOMER_VALUE_ADOPTION_VALIDATION_PHASES),
        "customer_manipulation": CUSTOMER_MANIPULATION_FIX_348,
        "automated_outreach": AUTOMATED_OUTREACH_FIX_348,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_348,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_348,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_348,
        "local_value_validation_executable": LOCAL_VALUE_VALIDATION_EXECUTABLE_FIX_348,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_348,
        "metrics_tracked": list(VALIDATION_METRICS),
        "metrics": metrics,
        "success_criteria": success,
        "composed_from_workstream_f1_delivered_solutions": True,
        "sections": sections,
        "fix_348_certification_requirements": list(FIX_348_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Customer value & adoption validation complete"
        if success.get("program_complete")
        else "Customer value & adoption validation composed — human review pending"
    )
    return CustomerValueAdoptionValidationProgramResult(
        ok=True,
        session_id=sid,
        customer_value_adoption_validation_program=board,
        blockers=blockers,
        detail=detail,
    )
