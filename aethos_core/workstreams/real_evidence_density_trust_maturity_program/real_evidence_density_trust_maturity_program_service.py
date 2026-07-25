# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_G1 / FIX 354 — real evidence density & trust maturity service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_354_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_contract import (
    AUTHORITY_EXPANSION_FIX_354,
    AUTOMATIC_EVIDENCE_ACCEPTANCE_FIX_354,
    CORE_PRINCIPLE,
    CUSTOMER_MANIPULATION_FIX_354,
    EVIDENCE_MATURITY_METRICS,
    EXECUTIVE_FIX_MODULES,
    FORBIDDEN_EVIDENCE_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_354,
    GOVERNANCE_MUTATION_FIX_354,
    GOVERNANCE_MUTATION_PERFORMED_FIX_354,
    LOCAL_EVIDENCE_MATURITY_EXECUTABLE_FIX_354,
    MUTATION_PERFORMED_FIX_354,
    PROGRAM_NON_GOALS,
    PROVIDER_MUTATION_FIX_354,
    REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PHASES,
    REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_FIX,
    REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_ID,
    REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_INVARIANT,
    REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_SCHEMA_VERSION,
    TRUST_AUTHORITY_FIX_354,
    TRUST_MUTATION_AUTHORITY_FIX_354,
    TRUST_PROMOTION_FIX_354,
)
from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_executor import (
    build_evidence_density_report,
    build_evidence_freshness_report,
    build_evidence_gap_registry,
    build_evidence_opportunity_registry,
    build_evidence_provenance_report,
    build_evidence_registry_inventory,
    build_trust_maturity_report,
    compute_evidence_maturity_metrics,
)
from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_store import (
    has_evidence_maturity_review_approve,
    list_evidence_maturity_records,
)


@dataclass(frozen=True)
class RealEvidenceDensityTrustMaturityProgramResult:
    ok: bool
    session_id: str
    real_evidence_density_trust_maturity_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_8_executive_visibility(*, program_session_id: str) -> dict[str, Any]:
    metrics = compute_evidence_maturity_metrics(program_session_id=program_session_id)
    trust = build_trust_maturity_report(program_session_id=program_session_id)
    return {
        "evidence_maturity_dashboard": {
            "dashboard_id": "evidence-maturity-dashboard",
            "program_session_id": program_session_id,
            "executive_fix_modules": list(EXECUTIVE_FIX_MODULES),
            "fix_314_public_launch_readiness_freeze": {
                "module": "FIX 314",
                "read_only": True,
                "trust_promotion_enabled": False,
            },
            "fix_315_launch_decision_package": {
                "module": "FIX 315",
                "read_only": True,
            },
            "fix_316_post_launch_operations_baseline": {
                "module": "FIX 316",
                "operational_proof_coverage": metrics.get("operational_proof_coverage"),
                "read_only": True,
            },
            "fix_330_executive_operating_system": {
                "module": "FIX 330",
                "evidence_density_score": metrics.get("evidence_density_score"),
                "read_only": True,
            },
            "workstream_f7_operating_model_reference": {
                "workstream": "WORKSTREAM_F7",
                "composed_read_only": True,
            },
            "evidence_maturity_metrics": metrics,
            "trust_maturity_summary": trust,
            "trust_authority_granted": False,
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, program_session_id: str) -> dict[str, Any]:
    records = _session_records(list_evidence_maturity_records(), session_id=program_session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "evidence_maturity_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("evidence_maturity_review_")]
    return {
        "evidence_maturity_review_registry": {
            "registry_id": "evidence-maturity-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "read_only": True,
        }
    }


def _success_criteria(*, program_session_id: str) -> dict[str, Any]:
    density = build_evidence_density_report(program_session_id=program_session_id)
    freshness = build_evidence_freshness_report(program_session_id=program_session_id)
    provenance = build_evidence_provenance_report(program_session_id=program_session_id)
    trust = build_trust_maturity_report(program_session_id=program_session_id)
    inventory = build_evidence_registry_inventory(program_session_id=program_session_id)
    metrics = compute_evidence_maturity_metrics(program_session_id=program_session_id)

    populated = sum(1 for s in inventory.get("sources") or [] if s.get("store_populated"))
    domains_with_evidence = sum(
        1 for stats in (provenance.get("provenance_by_domain") or {}).values() if stats.get("total", 0) > 0
    )

    return {
        "evidence_completeness_demonstrated": int(density.get("real_evidence_count") or 0) > 0,
        "evidence_freshness_demonstrated": float(freshness.get("evidence_freshness_score") or 0) >= 0,
        "evidence_diversity_demonstrated": domains_with_evidence >= 2,
        "evidence_provenance_demonstrated": populated > 0,
        "evidence_backed_confidence_demonstrated": float(metrics.get("evidence_density_score") or 0) > 0,
        "trust_authority_granted": False,
        "trust_promotion_performed": False,
        "program_complete": has_evidence_maturity_review_approve(program_session_id=program_session_id),
        "trust_maturity_score": trust.get("trust_maturity_score"),
    }


def build_real_evidence_density_trust_maturity_program(
    *, session_id: str = "default"
) -> RealEvidenceDensityTrustMaturityProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {
        "phase_1_evidence_registry_inventory": [
            {"evidence_registry_inventory": build_evidence_registry_inventory(program_session_id=sid)}
        ],
        "phase_2_evidence_density_analysis": [
            {"evidence_density_report": build_evidence_density_report(program_session_id=sid)}
        ],
        "phase_3_evidence_freshness_analysis": [
            {"evidence_freshness_report": build_evidence_freshness_report(program_session_id=sid)}
        ],
        "phase_4_evidence_provenance_analysis": [
            {"evidence_provenance_report": build_evidence_provenance_report(program_session_id=sid)}
        ],
        "phase_5_trust_maturity_analysis": [
            {"trust_maturity_report": build_trust_maturity_report(program_session_id=sid)}
        ],
        "phase_6_evidence_gap_registry": [
            {"evidence_gap_registry": build_evidence_gap_registry(program_session_id=sid)}
        ],
        "phase_7_evidence_opportunity_registry": [
            {"evidence_opportunity_registry": build_evidence_opportunity_registry(program_session_id=sid)}
        ],
        "phase_8_executive_visibility": [_build_phase_8_executive_visibility(program_session_id=sid)],
        "phase_9_human_review": [_build_phase_9_human_review(program_session_id=sid)],
    }

    success = _success_criteria(program_session_id=sid)
    metrics = compute_evidence_maturity_metrics(program_session_id=sid)

    if not success.get("evidence_completeness_demonstrated"):
        blockers.append("real_evidence_not_detected")
    if not has_evidence_maturity_review_approve(program_session_id=sid):
        blockers.append("evidence_maturity_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_SCHEMA_VERSION,
        "workstream_id": REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_ID,
        "fix_id": REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_354,
        "execution_performed": False,
        "core_principle": CORE_PRINCIPLE,
        "invariant": REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_EVIDENCE_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PHASES),
        "trust_authority": TRUST_AUTHORITY_FIX_354,
        "trust_promotion": TRUST_PROMOTION_FIX_354,
        "automatic_evidence_acceptance": AUTOMATIC_EVIDENCE_ACCEPTANCE_FIX_354,
        "customer_manipulation": CUSTOMER_MANIPULATION_FIX_354,
        "provider_mutation": PROVIDER_MUTATION_FIX_354,
        "governance_mutation": GOVERNANCE_MUTATION_FIX_354,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_354,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_354,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_354,
        "local_evidence_maturity_executable": LOCAL_EVIDENCE_MATURITY_EXECUTABLE_FIX_354,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_354,
        "metrics_tracked": list(EVIDENCE_MATURITY_METRICS),
        "metrics": metrics,
        "success_criteria": success,
        "composed_from_fix_300_through_330_et1_through_et5_and_workstreams_a_through_f7": True,
        "sections": sections,
        "fix_354_certification_requirements": list(FIX_354_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Real evidence density & trust maturity validation complete"
        if success.get("program_complete")
        else "Evidence maturity validation composed — human review pending"
    )
    return RealEvidenceDensityTrustMaturityProgramResult(
        ok=True,
        session_id=sid,
        real_evidence_density_trust_maturity_program=board,
        blockers=blockers,
        detail=detail,
    )
