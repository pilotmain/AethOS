# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F1 / FIX 347 — first customer delivery pilot service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_347_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_contract import (
    AUTHORITY_EXPANSION_FIX_347,
    AUTOMATIC_CUSTOMER_ACCEPTANCE_FIX_347,
    CORE_PRINCIPLE,
    CUSTOMER_AUTHORITY_FIX_347,
    EXECUTIVE_FIX_MODULES,
    FIRST_CUSTOMER_DELIVERY_PILOT_PHASES,
    FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_FIX,
    FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_ID,
    FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_INVARIANT,
    FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_SCHEMA_VERSION,
    FORBIDDEN_PILOT_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_347,
    GOVERNANCE_MUTATION_PERFORMED_FIX_347,
    LOCAL_CUSTOMER_PILOT_EXECUTABLE_FIX_347,
    MUTATION_PERFORMED_FIX_347,
    PILOT_METRICS,
    PILOT_REQUEST_LABELS,
    PROGRAM_NON_GOALS,
    RECOMMENDED_PILOT_REQUEST_TYPES,
    TRUST_MUTATION_AUTHORITY_FIX_347,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_executor import (
    build_customer_delivery_plan,
    build_customer_feedback_report,
    build_customer_value_realization_report,
    build_delivery_risk_summary,
    build_scope_boundary_report,
    compute_pilot_metrics,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_store import (
    get_latest_customer_delivery_request,
    has_customer_pilot_review_approve,
    list_customer_pilot_run_registry_entries,
    list_first_customer_delivery_pilot_records,
)


@dataclass(frozen=True)
class FirstCustomerDeliveryPilotProgramResult:
    ok: bool
    session_id: str
    first_customer_delivery_pilot_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _latest_run(*, session_id: str) -> dict[str, Any]:
    runs = [
        row
        for row in list_customer_pilot_run_registry_entries()
        if str(row.get("session_id") or "") == session_id
    ]
    return runs[-1] if runs else {}


def _build_phase_10_pilot_review(*, session_id: str) -> dict[str, Any]:
    records = _session_records(list_first_customer_delivery_pilot_records(), session_id=session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "customer_pilot_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("customer_pilot_review_")]
    return {
        "customer_pilot_review_registry": {
            "registry_id": "customer-pilot-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "read_only": True,
        }
    }


def _success_criteria(*, session_id: str) -> dict[str, Any]:
    request = get_latest_customer_delivery_request(session_id=session_id)
    latest = _latest_run(session_id=session_id)
    metrics = compute_pilot_metrics(session_id=session_id)
    return {
        "customer_request_captured": request is not None,
        "delivery_plan_composed": request is not None,
        "pilot_execution_completed": bool(latest),
        "certification_evidence_present": bool(latest.get("certification")),
        "customer_feedback_composed": True,
        "value_realization_composed": metrics.get("value_realized") is True or bool(latest),
        "customer_authority_granted": False,
        "automatic_customer_acceptance": False,
        "program_complete": has_customer_pilot_review_approve(session_id=session_id),
    }


def build_first_customer_delivery_pilot_program(
    *, session_id: str = "default"
) -> FirstCustomerDeliveryPilotProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []
    request = get_latest_customer_delivery_request(session_id=sid)
    latest = _latest_run(session_id=sid)
    stage_results = latest.get("stage_results") or {}

    sections: dict[str, list[dict[str, Any]]] = {
        "phase_1_customer_request_intake": [
            {
                "customer_delivery_request": request,
                "scope_boundary_report": build_scope_boundary_report(session_id=sid),
            }
        ],
        "phase_2_delivery_planning": [
            {
                "customer_delivery_plan": build_customer_delivery_plan(session_id=sid),
                "delivery_risk_summary": build_delivery_risk_summary(session_id=sid),
            }
        ],
        "phase_3_workspace_creation": [
            {
                "customer_workspace_report": stage_results.get("workspace"),
                "workspace_evidence": stage_results.get("workspace"),
            }
        ],
        "phase_4_code_generation": [
            {
                "customer_code_generation_report": stage_results.get("generation"),
                "changeset_review_package": stage_results.get("generation"),
            }
        ],
        "phase_5_git_delivery": [
            {
                "customer_git_delivery_report": stage_results.get("git_delivery"),
                "pull_request_report": stage_results.get("git_delivery"),
            }
        ],
        "phase_6_deployment": [
            {
                "customer_deployment_report": stage_results.get("deployment"),
                "deployment_verification_report": stage_results.get("deployment"),
            }
        ],
        "phase_7_end_to_end_certification": [
            {
                "customer_delivery_certification_report": latest.get("certification"),
                "delivery_evidence_bundle": {
                    "run_id": latest.get("run_id"),
                    "passed": latest.get("passed"),
                    "scenario_id": latest.get("scenario_id"),
                },
            }
        ],
        "phase_8_customer_feedback": [
            {"customer_feedback_report": build_customer_feedback_report(session_id=sid)}
        ],
        "phase_9_value_realization": [
            {"customer_value_realization_report": build_customer_value_realization_report(session_id=sid)}
        ],
        "phase_10_pilot_review": [_build_phase_10_pilot_review(session_id=sid)],
    }

    success = _success_criteria(session_id=sid)
    if request is None:
        blockers.append("customer_delivery_request_required")
    if not has_customer_pilot_review_approve(session_id=sid):
        blockers.append("customer_pilot_review_approve_required")

    metrics = compute_pilot_metrics(session_id=sid)
    board: dict[str, Any] = {
        "schema_version": FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_SCHEMA_VERSION,
        "workstream_id": FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_ID,
        "fix_id": FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_347,
        "execution_performed": True,
        "core_principle": CORE_PRINCIPLE,
        "invariant": FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_PILOT_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(FIRST_CUSTOMER_DELIVERY_PILOT_PHASES),
        "recommended_request_types": list(RECOMMENDED_PILOT_REQUEST_TYPES),
        "request_type_labels": dict(PILOT_REQUEST_LABELS),
        "customer_authority": CUSTOMER_AUTHORITY_FIX_347,
        "automatic_customer_acceptance": AUTOMATIC_CUSTOMER_ACCEPTANCE_FIX_347,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_347,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_347,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_347,
        "local_customer_pilot_executable": LOCAL_CUSTOMER_PILOT_EXECUTABLE_FIX_347,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_347,
        "metrics_tracked": list(PILOT_METRICS),
        "metrics": metrics,
        "success_criteria": success,
        "executive_fix_modules": list(EXECUTIVE_FIX_MODULES),
        "sections": sections,
        "fix_347_certification_requirements": list(FIX_347_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "First customer delivery pilot complete"
        if success.get("program_complete")
        else "First customer delivery pilot composed — human review pending"
    )
    return FirstCustomerDeliveryPilotProgramResult(
        ok=True,
        session_id=sid,
        first_customer_delivery_pilot_program=board,
        blockers=blockers,
        detail=detail,
    )
