# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_G4 / FIX 357 — enterprise platform maturity & readiness audit service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_357_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.enterprise_platform_maturity_readiness_audit_program.enterprise_platform_maturity_readiness_audit_program_contract import (
    AUTHORITY_EXPANSION_FIX_357,
    BUSINESS_AUTOMATION_FIX_357,
    CORE_PRINCIPLE,
    ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PHASES,
    ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_FIX,
    ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_ID,
    ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_INVARIANT,
    ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_SCHEMA_VERSION,
    EXECUTIVE_FIX_MODULES,
    EXECUTIVE_WORKSTREAM_MODULES,
    FORBIDDEN_MATURITY_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_357,
    GOVERNANCE_MUTATION_FIX_357,
    GOVERNANCE_MUTATION_PERFORMED_FIX_357,
    LAUNCH_AUTHORITY_FIX_357,
    LOCAL_PLATFORM_MATURITY_EXECUTABLE_FIX_357,
    MUTATION_PERFORMED_FIX_357,
    PLATFORM_MATURITY_METRICS,
    PROGRAM_NON_GOALS,
    TRUST_MUTATION_AUTHORITY_FIX_357,
    TRUST_PROMOTION_FIX_357,
)
from aethos_core.workstreams.enterprise_platform_maturity_readiness_audit_program.enterprise_platform_maturity_readiness_audit_program_executor import (
    build_architecture_maturity_report,
    build_customer_commercial_maturity_report,
    build_evidence_trust_maturity_report,
    build_execution_maturity_report,
    build_operational_maturity_report,
    build_platform_gap_registry,
    build_platform_inventory_registry,
    compute_platform_maturity_metrics,
)
from aethos_core.workstreams.enterprise_platform_maturity_readiness_audit_program.enterprise_platform_maturity_readiness_audit_program_store import (
    has_platform_maturity_review_approve,
    list_platform_maturity_records,
)


@dataclass(frozen=True)
class EnterprisePlatformMaturityReadinessAuditProgramResult:
    ok: bool
    session_id: str
    enterprise_platform_maturity_readiness_audit_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_8_executive_visibility(*, program_session_id: str) -> dict[str, Any]:
    metrics = compute_platform_maturity_metrics(program_session_id=program_session_id)
    gaps = build_platform_gap_registry(program_session_id=program_session_id)
    return {
        "enterprise_platform_maturity_dashboard": {
            "dashboard_id": "enterprise-platform-maturity-dashboard",
            "program_session_id": program_session_id,
            "executive_fix_modules": list(EXECUTIVE_FIX_MODULES),
            "executive_workstream_modules": list(EXECUTIVE_WORKSTREAM_MODULES),
            "fix_330_executive_operating_system": {
                "module": "FIX 330",
                "overall_platform_maturity_score": metrics.get("overall_platform_maturity_score"),
                "launch_authority_granted": False,
            },
            "workstream_f7_operating_model_reference": {
                "workstream": "WORKSTREAM_F7",
                "composed_read_only": True,
            },
            "workstream_g1_evidence_maturity_reference": {
                "workstream": "WORKSTREAM_G1",
                "evidence_maturity_score": metrics.get("evidence_maturity_score"),
                "composed_read_only": True,
            },
            "workstream_g2_usage_adoption_reference": {
                "workstream": "WORKSTREAM_G2",
                "customer_maturity_score": metrics.get("customer_maturity_score"),
                "composed_read_only": True,
            },
            "workstream_g3_business_viability_reference": {
                "workstream": "WORKSTREAM_G3",
                "commercial_maturity_score": metrics.get("commercial_maturity_score"),
                "composed_read_only": True,
            },
            "platform_maturity_metrics": metrics,
            "platform_maturity_level": metrics.get("platform_maturity_level"),
            "open_gap_count": gaps.get("gap_count"),
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, program_session_id: str) -> dict[str, Any]:
    records = _session_records(list_platform_maturity_records(), session_id=program_session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "platform_maturity_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("platform_maturity_review_")]
    return {
        "platform_maturity_review_registry": {
            "registry_id": "platform-maturity-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "read_only": True,
        }
    }


def _success_criteria(*, program_session_id: str) -> dict[str, Any]:
    inventory = build_platform_inventory_registry(program_session_id=program_session_id)
    architecture = build_architecture_maturity_report(program_session_id=program_session_id)
    execution = build_execution_maturity_report(program_session_id=program_session_id)
    operational = build_operational_maturity_report(program_session_id=program_session_id)
    customer = build_customer_commercial_maturity_report(program_session_id=program_session_id)
    evidence = build_evidence_trust_maturity_report(program_session_id=program_session_id)
    metrics = compute_platform_maturity_metrics(program_session_id=program_session_id)

    return {
        "platform_inventory_complete": inventory.get("inventory_complete") is True,
        "architecture_maturity_assessed": float(architecture.get("architecture_maturity_score") or 0) > 0,
        "execution_maturity_assessed": execution.get("execution_maturity_demonstrated") is True,
        "operational_maturity_assessed": operational.get("operational_maturity_demonstrated") is True,
        "customer_maturity_assessed": customer.get("customer_commercial_maturity_demonstrated") is True,
        "commercial_maturity_assessed": float(customer.get("commercial_maturity_score") or 0) >= 0,
        "evidence_maturity_assessed": evidence.get("evidence_trust_maturity_demonstrated") is True,
        "enterprise_readiness_signals": float(metrics.get("overall_platform_maturity_score") or 0) >= 0.4,
        "launch_authority_granted": False,
        "trust_promotion_performed": False,
        "program_complete": has_platform_maturity_review_approve(program_session_id=program_session_id),
    }


def build_enterprise_platform_maturity_readiness_audit_program(
    *, session_id: str = "default"
) -> EnterprisePlatformMaturityReadinessAuditProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {
        "phase_1_platform_inventory": [
            {"platform_inventory_registry": build_platform_inventory_registry(program_session_id=sid)}
        ],
        "phase_2_architecture_maturity_audit": [
            {"architecture_maturity_report": build_architecture_maturity_report(program_session_id=sid)}
        ],
        "phase_3_execution_maturity_audit": [
            {"execution_maturity_report": build_execution_maturity_report(program_session_id=sid)}
        ],
        "phase_4_operational_maturity_audit": [
            {"operational_maturity_report": build_operational_maturity_report(program_session_id=sid)}
        ],
        "phase_5_customer_commercial_maturity_audit": [
            {"customer_commercial_maturity_report": build_customer_commercial_maturity_report(program_session_id=sid)}
        ],
        "phase_6_evidence_trust_maturity_audit": [
            {"evidence_trust_maturity_report": build_evidence_trust_maturity_report(program_session_id=sid)}
        ],
        "phase_7_platform_gap_registry": [
            {"platform_gap_registry": build_platform_gap_registry(program_session_id=sid)}
        ],
        "phase_8_executive_visibility": [_build_phase_8_executive_visibility(program_session_id=sid)],
        "phase_9_human_review": [_build_phase_9_human_review(program_session_id=sid)],
    }

    success = _success_criteria(program_session_id=sid)
    metrics = compute_platform_maturity_metrics(program_session_id=sid)

    if not success.get("platform_inventory_complete"):
        blockers.append("platform_inventory_incomplete")
    if not has_platform_maturity_review_approve(program_session_id=sid):
        blockers.append("platform_maturity_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_SCHEMA_VERSION,
        "workstream_id": ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_ID,
        "fix_id": ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_357,
        "execution_performed": False,
        "core_principle": CORE_PRINCIPLE,
        "invariant": ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_MATURITY_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PHASES),
        "launch_authority": LAUNCH_AUTHORITY_FIX_357,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_357,
        "governance_mutation": GOVERNANCE_MUTATION_FIX_357,
        "trust_promotion": TRUST_PROMOTION_FIX_357,
        "business_automation": BUSINESS_AUTOMATION_FIX_357,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_357,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_357,
        "local_platform_maturity_executable": LOCAL_PLATFORM_MATURITY_EXECUTABLE_FIX_357,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_357,
        "metrics_tracked": list(PLATFORM_MATURITY_METRICS),
        "metrics": metrics,
        "success_criteria": success,
        "composed_from_fix_300_through_330_et1_through_et5_f1_through_g3": True,
        "sections": sections,
        "fix_357_certification_requirements": list(FIX_357_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Enterprise platform maturity & readiness audit complete"
        if success.get("program_complete")
        else "Platform maturity audit composed — human review pending"
    )
    return EnterprisePlatformMaturityReadinessAuditProgramResult(
        ok=True,
        session_id=sid,
        enterprise_platform_maturity_readiness_audit_program=board,
        blockers=blockers,
        detail=detail,
    )
