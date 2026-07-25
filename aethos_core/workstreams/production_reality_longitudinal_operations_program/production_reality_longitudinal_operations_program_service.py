# SPDX-License-Identifier: Apache-2.0
"""PHASE_J1 / FIX 364 — production reality longitudinal operations service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_364_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.production_reality_longitudinal_operations_program.production_reality_longitudinal_operations_program_contract import (
    APPROVAL_BYPASS_FIX_364,
    AUTHORITY_EXPANSION_FIX_364,
    AUTONOMOUS_PRODUCTION_CONTROL_FIX_364,
    CORE_PRINCIPLE,
    DURABILITY_LEVELS,
    EXECUTIVE_WORKSTREAM_MODULES,
    FORBIDDEN_PRODUCTION_REALITY_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_364,
    GOVERNANCE_BYPASS_FIX_364,
    GOVERNANCE_MUTATION_FIX_364,
    GOVERNANCE_MUTATION_PERFORMED_FIX_364,
    LOCAL_PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_EXECUTABLE_FIX_364,
    MUTATION_PERFORMED_FIX_364,
    OPERATIONAL_AUTHORITY_FIX_364,
    OPERATIONAL_AUTOMATION_CHANGES_FIX_364,
    PRODUCTION_OPERATIONS_MIN_SIZE,
    PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PHASES,
    PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_FIX,
    PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_ID,
    PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_INVARIANT,
    PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_SCHEMA_VERSION,
    PRODUCTION_REALITY_METRICS,
    PRODUCTION_SUSTAINED_MIN_SIZE,
    PROGRAM_NON_GOALS,
    TRUST_MUTATION_AUTHORITY_FIX_364,
    TRUST_PROMOTION_FIX_364,
)
from aethos_core.workstreams.production_reality_longitudinal_operations_program.production_reality_longitudinal_operations_program_executor import (
    build_customer_reality_report,
    build_deployment_durability_report,
    build_durability_opportunity_registry,
    build_production_incident_report,
    build_production_operations_registry,
    build_provider_reality_report,
    build_recovery_durability_report,
    compute_production_reality_metrics,
)
from aethos_core.workstreams.production_reality_longitudinal_operations_program.production_reality_longitudinal_operations_program_store import (
    has_production_reality_review_approve,
    list_production_reality_records,
)


@dataclass(frozen=True)
class ProductionRealityLongitudinalOperationsProgramResult:
    ok: bool
    session_id: str
    production_reality_longitudinal_operations_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_8_executive_visibility(*, program_session_id: str) -> dict[str, Any]:
    metrics = compute_production_reality_metrics(program_session_id=program_session_id)
    return {
        "production_reality_dashboard": {
            "dashboard_id": "production-reality-dashboard",
            "program_session_id": program_session_id,
            "executive_workstream_modules": list(EXECUTIVE_WORKSTREAM_MODULES),
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
            "workstream_f7_business_operating_model_reference": {
                "workstream": "WORKSTREAM_F7",
                "composed_read_only": True,
            },
            "production_reality_metrics": metrics,
            "durability_level": metrics.get("durability_level"),
            "operational_authority_granted": False,
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, program_session_id: str) -> dict[str, Any]:
    records = _session_records(list_production_reality_records(), session_id=program_session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "production_reality_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("production_reality_review_")]
    return {
        "production_reality_review_registry": {
            "registry_id": "production-reality-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "read_only": True,
        }
    }


def _success_criteria(*, program_session_id: str) -> dict[str, Any]:
    registry = build_production_operations_registry(program_session_id=program_session_id)
    deployment = build_deployment_durability_report(program_session_id=program_session_id)
    recovery = build_recovery_durability_report(program_session_id=program_session_id)
    provider = build_provider_reality_report(program_session_id=program_session_id)
    customer = build_customer_reality_report(program_session_id=program_session_id)
    metrics = compute_production_reality_metrics(program_session_id=program_session_id)

    return {
        "production_operations_registry_demonstrated": registry.get("operation_count", 0) >= PRODUCTION_OPERATIONS_MIN_SIZE,
        "sustained_operation_demonstrated": int(registry.get("operation_count") or 0) >= PRODUCTION_SUSTAINED_MIN_SIZE,
        "deployment_durability_demonstrated": deployment.get("deployment_durability_demonstrated") is True,
        "recovery_durability_demonstrated": recovery.get("recovery_durability_demonstrated") is True,
        "provider_durability_demonstrated": provider.get("provider_reality_demonstrated") is True,
        "customer_durability_demonstrated": customer.get("customer_reality_demonstrated") is True,
        "production_reality_signals": float(metrics.get("operational_durability_score") or 0) >= 0.35,
        "operational_authority_granted": False,
        "approval_bypass_performed": False,
        "program_complete": has_production_reality_review_approve(program_session_id=program_session_id),
    }


def build_production_reality_longitudinal_operations_program(
    *, session_id: str = "default"
) -> ProductionRealityLongitudinalOperationsProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {
        "phase_1_production_operations_registry": [
            {"production_operations_registry": build_production_operations_registry(program_session_id=sid)}
        ],
        "phase_2_deployment_durability_analysis": [
            {"deployment_durability_report": build_deployment_durability_report(program_session_id=sid)}
        ],
        "phase_3_incident_reality_analysis": [
            {"production_incident_report": build_production_incident_report(program_session_id=sid)}
        ],
        "phase_4_recovery_durability_analysis": [
            {"recovery_durability_report": build_recovery_durability_report(program_session_id=sid)}
        ],
        "phase_5_provider_reality_analysis": [
            {"provider_reality_report": build_provider_reality_report(program_session_id=sid)}
        ],
        "phase_6_customer_reality_analysis": [
            {"customer_reality_report": build_customer_reality_report(program_session_id=sid)}
        ],
        "phase_7_durability_opportunity_registry": [
            {"durability_opportunity_registry": build_durability_opportunity_registry(program_session_id=sid)}
        ],
        "phase_8_executive_visibility": [_build_phase_8_executive_visibility(program_session_id=sid)],
        "phase_9_human_review": [_build_phase_9_human_review(program_session_id=sid)],
    }

    success = _success_criteria(program_session_id=sid)
    metrics = compute_production_reality_metrics(program_session_id=sid)
    operation_count = build_production_operations_registry(program_session_id=sid).get("operation_count", 0)

    if operation_count < PRODUCTION_OPERATIONS_MIN_SIZE:
        blockers.append("production_operations_minimum_not_met")
    if not has_production_reality_review_approve(program_session_id=sid):
        blockers.append("production_reality_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_SCHEMA_VERSION,
        "phase_id": PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_ID,
        "workstream_id": PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_ID,
        "fix_id": PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_364,
        "core_principle": CORE_PRINCIPLE,
        "invariant": PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_PRODUCTION_REALITY_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PHASES),
        "operational_authority": OPERATIONAL_AUTHORITY_FIX_364,
        "autonomous_production_control": AUTONOMOUS_PRODUCTION_CONTROL_FIX_364,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_364,
        "governance_mutation": GOVERNANCE_MUTATION_FIX_364,
        "governance_bypass": GOVERNANCE_BYPASS_FIX_364,
        "trust_promotion": TRUST_PROMOTION_FIX_364,
        "approval_bypass": APPROVAL_BYPASS_FIX_364,
        "operational_automation_changes": OPERATIONAL_AUTOMATION_CHANGES_FIX_364,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_364,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_364,
        "local_production_reality_longitudinal_operations_executable": LOCAL_PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_EXECUTABLE_FIX_364,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_364,
        "production_operations_minimum_size": PRODUCTION_OPERATIONS_MIN_SIZE,
        "production_sustained_minimum_size": PRODUCTION_SUSTAINED_MIN_SIZE,
        "durability_levels": list(DURABILITY_LEVELS),
        "metrics_tracked": list(PRODUCTION_REALITY_METRICS),
        "metrics": metrics,
        "success_criteria": success,
        "composed_from_phase_i3_g4_h3_fix330_f7_patterns": True,
        "sections": sections,
        "fix_364_certification_requirements": list(FIX_364_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Production reality longitudinal operations program complete"
        if success.get("program_complete")
        else "Production reality composed — human review pending"
    )
    return ProductionRealityLongitudinalOperationsProgramResult(
        ok=True,
        session_id=sid,
        production_reality_longitudinal_operations_program=board,
        blockers=blockers,
        detail=detail,
    )
