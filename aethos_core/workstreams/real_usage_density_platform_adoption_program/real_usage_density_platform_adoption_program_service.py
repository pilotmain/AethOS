# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_G2 / FIX 355 — real usage density & platform adoption service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_355_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.real_usage_density_platform_adoption_program.real_usage_density_platform_adoption_program_contract import (
    AUTHORITY_EXPANSION_FIX_355,
    AUTOMATED_OUTREACH_FIX_355,
    BEHAVIORAL_MANIPULATION_FIX_355,
    CORE_PRINCIPLE,
    EXECUTIVE_FIX_MODULES,
    FORBIDDEN_USAGE_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_355,
    GOVERNANCE_MUTATION_PERFORMED_FIX_355,
    LOCAL_USAGE_ADOPTION_EXECUTABLE_FIX_355,
    MUTATION_PERFORMED_FIX_355,
    PLAN_MUTATION_FIX_355,
    PROGRAM_NON_GOALS,
    REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PHASES,
    REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_FIX,
    REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_ID,
    REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_INVARIANT,
    REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_SCHEMA_VERSION,
    TRUST_MUTATION_AUTHORITY_FIX_355,
    TRUST_MUTATION_FIX_355,
    USAGE_ADOPTION_METRICS,
    USER_AUTHORITY_FIX_355,
)
from aethos_core.workstreams.real_usage_density_platform_adoption_program.real_usage_density_platform_adoption_program_executor import (
    build_active_usage_report,
    build_adoption_friction_report,
    build_adoption_opportunity_registry,
    build_platform_dependence_report,
    build_retained_usage_report,
    build_usage_registry_inventory,
    build_workflow_adoption_report,
    compute_usage_adoption_metrics,
)
from aethos_core.workstreams.real_usage_density_platform_adoption_program.real_usage_density_platform_adoption_program_store import (
    has_platform_adoption_review_approve,
    list_platform_adoption_records,
)


@dataclass(frozen=True)
class RealUsageDensityPlatformAdoptionProgramResult:
    ok: bool
    session_id: str
    real_usage_density_platform_adoption_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_8_executive_visibility(*, program_session_id: str) -> dict[str, Any]:
    metrics = compute_usage_adoption_metrics(program_session_id=program_session_id)
    dependence = build_platform_dependence_report(program_session_id=program_session_id)
    return {
        "platform_adoption_dashboard": {
            "dashboard_id": "platform-adoption-dashboard",
            "program_session_id": program_session_id,
            "executive_fix_modules": list(EXECUTIVE_FIX_MODULES),
            "fix_318_product_analytics": {
                "module": "FIX 318",
                "active_users": metrics.get("active_users"),
                "read_only": True,
            },
            "fix_320_growth_adoption": {
                "module": "FIX 320",
                "workflow_adoption_rate": metrics.get("workflow_adoption_rate"),
                "read_only": True,
            },
            "fix_321_product_market_fit": {
                "module": "FIX 321",
                "retained_users": metrics.get("retained_users"),
                "read_only": True,
            },
            "fix_330_executive_operating_system": {
                "module": "FIX 330",
                "platform_dependence_score": metrics.get("platform_dependence_score"),
                "read_only": True,
            },
            "workstream_g1_evidence_maturity_reference": {
                "workstream": "WORKSTREAM_G1",
                "composed_read_only": True,
            },
            "usage_adoption_metrics": metrics,
            "usage_maturity_distribution": dependence.get("usage_maturity_distribution"),
            "user_authority_granted": False,
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, program_session_id: str) -> dict[str, Any]:
    records = _session_records(list_platform_adoption_records(), session_id=program_session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "platform_adoption_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("platform_adoption_review_")]
    return {
        "platform_adoption_review_registry": {
            "registry_id": "platform-adoption-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "read_only": True,
        }
    }


def _success_criteria(*, program_session_id: str) -> dict[str, Any]:
    active = build_active_usage_report(program_session_id=program_session_id)
    retained = build_retained_usage_report(program_session_id=program_session_id)
    workflow = build_workflow_adoption_report(program_session_id=program_session_id)
    dependence = build_platform_dependence_report(program_session_id=program_session_id)
    metrics = compute_usage_adoption_metrics(program_session_id=program_session_id)
    return {
        "active_usage_demonstrated": active.get("active_usage_demonstrated") is True,
        "recurring_usage_demonstrated": int(retained.get("recurring_workflows") or 0) > 0,
        "retained_usage_demonstrated": retained.get("retained_usage_demonstrated") is True,
        "expanding_usage_demonstrated": float(workflow.get("workflow_adoption_rate") or 0) > 0,
        "workflow_dependence_demonstrated": dependence.get("workflow_dependence_demonstrated") is True,
        "user_authority_granted": False,
        "automated_outreach_performed": False,
        "program_complete": has_platform_adoption_review_approve(program_session_id=program_session_id),
        "platform_dependence_score": metrics.get("platform_dependence_score"),
    }


def build_real_usage_density_platform_adoption_program(
    *, session_id: str = "default"
) -> RealUsageDensityPlatformAdoptionProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {
        "phase_1_usage_registry_inventory": [
            {"usage_registry_inventory": build_usage_registry_inventory(program_session_id=sid)}
        ],
        "phase_2_active_usage_analysis": [
            {"active_usage_report": build_active_usage_report(program_session_id=sid)}
        ],
        "phase_3_workflow_adoption_analysis": [
            {"workflow_adoption_report": build_workflow_adoption_report(program_session_id=sid)}
        ],
        "phase_4_retained_usage_analysis": [
            {"retained_usage_report": build_retained_usage_report(program_session_id=sid)}
        ],
        "phase_5_platform_dependence_analysis": [
            {"platform_dependence_report": build_platform_dependence_report(program_session_id=sid)}
        ],
        "phase_6_adoption_friction_analysis": [
            {"adoption_friction_report": build_adoption_friction_report(program_session_id=sid)}
        ],
        "phase_7_adoption_opportunity_registry": [
            {"adoption_opportunity_registry": build_adoption_opportunity_registry(program_session_id=sid)}
        ],
        "phase_8_executive_visibility": [_build_phase_8_executive_visibility(program_session_id=sid)],
        "phase_9_human_review": [_build_phase_9_human_review(program_session_id=sid)],
    }

    success = _success_criteria(program_session_id=sid)
    metrics = compute_usage_adoption_metrics(program_session_id=sid)

    if not success.get("active_usage_demonstrated"):
        blockers.append("active_usage_not_detected")
    if not has_platform_adoption_review_approve(program_session_id=sid):
        blockers.append("platform_adoption_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_SCHEMA_VERSION,
        "workstream_id": REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_ID,
        "fix_id": REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_355,
        "execution_performed": False,
        "core_principle": CORE_PRINCIPLE,
        "invariant": REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_USAGE_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PHASES),
        "user_authority": USER_AUTHORITY_FIX_355,
        "automated_outreach": AUTOMATED_OUTREACH_FIX_355,
        "behavioral_manipulation": BEHAVIORAL_MANIPULATION_FIX_355,
        "plan_mutation": PLAN_MUTATION_FIX_355,
        "trust_mutation": TRUST_MUTATION_FIX_355,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_355,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_355,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_355,
        "local_usage_adoption_executable": LOCAL_USAGE_ADOPTION_EXECUTABLE_FIX_355,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_355,
        "metrics_tracked": list(USAGE_ADOPTION_METRICS),
        "metrics": metrics,
        "success_criteria": success,
        "composed_from_g1_f1_f2_et1_through_et5_and_fix_318_320_321_330": True,
        "sections": sections,
        "fix_355_certification_requirements": list(FIX_355_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Real usage density & platform adoption validation complete"
        if success.get("program_complete")
        else "Platform adoption validation composed — human review pending"
    )
    return RealUsageDensityPlatformAdoptionProgramResult(
        ok=True,
        session_id=sid,
        real_usage_density_platform_adoption_program=board,
        blockers=blockers,
        detail=detail,
    )
