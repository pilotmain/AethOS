# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_D2 / FIX 342 — compose multi-cloud operational proof program."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_342_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_contract import (
    ALL_PROOF_PROVIDERS,
    AUTHORITY_EXPANSION_FIX_342,
    CORE_PRINCIPLE,
    EXECUTIVE_FIX_MODULES,
    FORBIDDEN_PROOF_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_342,
    GOVERNANCE_MUTATION_PERFORMED_FIX_342,
    LOCAL_MULTI_CLOUD_PROOF_EXECUTABLE_FIX_342,
    MULTI_CLOUD_OPERATIONAL_PROOF_PHASES,
    MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_FIX,
    MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_ID,
    MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_INVARIANT,
    MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_342,
    PROGRAM_NON_GOALS,
    PROVIDER_AUTHORITY_FIX_342,
    TRUST_MUTATION_AUTHORITY_FIX_342,
    WAVE_1_PROVIDERS,
)
from aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_executor import (
    build_deployment_candidate_registry,
    build_provider_evidence_bundle,
    build_provider_failure_report,
    build_provider_maturity_scorecard,
    build_provider_reliability_report,
)
from aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_store import (
    has_provider_proof_review_approve,
    list_multi_cloud_operational_proof_records,
    list_provider_execution_registry_entries,
    list_provider_verification_registry_entries,
)


@dataclass(frozen=True)
class MultiCloudOperationalProofProgramResult:
    ok: bool
    session_id: str
    multi_cloud_operational_proof_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_2_multi_cloud_execution(*, session_id: str) -> dict[str, Any]:
    executions = [
        row for row in list_provider_execution_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    return {
        "provider_execution_registry": {
            "registry_id": "provider-execution-registry",
            "execution_count": len(executions),
            "executions": executions[-20:],
            "et4_deployment_flows": True,
            "read_only": True,
        }
    }


def _build_phase_3_verification(*, session_id: str) -> dict[str, Any]:
    verifications = [
        row for row in list_provider_verification_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    return {
        "provider_verification_registry": {
            "registry_id": "provider-verification-registry",
            "verification_count": len(verifications),
            "verifications": verifications[-20:],
            "checks": ["deployment_success", "endpoint_availability", "health_checks", "environment_integrity"],
            "read_only": True,
        }
    }


def _build_phase_8_executive_visibility(*, session_id: str) -> dict[str, Any]:
    scorecard = build_provider_maturity_scorecard(session_id=session_id)
    reliability = build_provider_reliability_report(session_id=session_id)
    module_assessments = {
        fix_label: {"multi_cloud_proof_representable": True, "compose_available": True}
        for fix_label in EXECUTIVE_FIX_MODULES
    }
    return {
        "multi_cloud_dashboard": {
            "dashboard_id": "multi-cloud-dashboard",
            "providers": list(ALL_PROOF_PROVIDERS),
            "wave_1_providers": list(WAVE_1_PROVIDERS),
            "wave_1_multi_cloud_proven": scorecard.get("wave_1_multi_cloud_proven"),
            "module_assessments": module_assessments,
            "reliability_summary": reliability.get("per_provider"),
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, session_id: str) -> dict[str, Any]:
    records = _session_records(list_multi_cloud_operational_proof_records(), session_id=session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "provider_proof_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("provider_proof_review_")]
    return {
        "provider_proof_review_registry": {
            "registry_id": "provider-proof-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "read_only": True,
        }
    }


def _success_criteria(*, session_id: str) -> dict[str, Any]:
    executions = [
        row for row in list_provider_execution_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    scorecard = build_provider_maturity_scorecard(session_id=session_id)
    wave1_executions = [row for row in executions if row.get("provider") in WAVE_1_PROVIDERS and row.get("passed")]

    return {
        "multi_cloud_deployments_demonstrated": len(wave1_executions) >= 1,
        "evidence_captured": len(executions) >= 1,
        "reliability_measured": bool(build_provider_reliability_report(session_id=session_id).get("per_provider")),
        "wave_1_multi_cloud_proven": scorecard.get("wave_1_multi_cloud_proven") is True,
        "provider_authority_granted": False,
        "governance_unchanged": True,
        "program_complete": (
            len(wave1_executions) >= len(WAVE_1_PROVIDERS)
            and has_provider_proof_review_approve(session_id=session_id)
            and scorecard.get("wave_1_multi_cloud_proven") is True
        ),
    }


def build_multi_cloud_operational_proof_program(
    *, session_id: str = "default"
) -> MultiCloudOperationalProofProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {}
    phase_builders = (
        lambda session_id=sid: {"deployment_candidate_registry": build_deployment_candidate_registry(session_id=session_id)},
        _build_phase_2_multi_cloud_execution,
        _build_phase_3_verification,
        lambda session_id=sid: {"provider_reliability_report": build_provider_reliability_report(session_id=session_id)},
        lambda session_id=sid: {"provider_failure_report": build_provider_failure_report(session_id=session_id)},
        lambda session_id=sid: {"provider_evidence_bundle": build_provider_evidence_bundle(session_id=session_id)},
        lambda session_id=sid: {"provider_maturity_scorecard": build_provider_maturity_scorecard(session_id=session_id)},
        _build_phase_8_executive_visibility,
        _build_phase_9_human_review,
    )
    for phase, builder in zip(MULTI_CLOUD_OPERATIONAL_PROOF_PHASES, phase_builders, strict=True):
        sections[phase] = [builder(session_id=sid)]

    success = _success_criteria(session_id=sid)
    if not success.get("multi_cloud_deployments_demonstrated"):
        blockers.append("provider_proof_executions_pending")
    if not has_provider_proof_review_approve(session_id=sid):
        blockers.append("provider_proof_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_SCHEMA_VERSION,
        "workstream_id": MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_ID,
        "fix_id": MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_342,
        "execution_performed": success.get("multi_cloud_deployments_demonstrated") is True,
        "core_principle": CORE_PRINCIPLE,
        "invariant": MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_PROOF_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(MULTI_CLOUD_OPERATIONAL_PROOF_PHASES),
        "all_proof_providers": list(ALL_PROOF_PROVIDERS),
        "wave_1_providers": list(WAVE_1_PROVIDERS),
        "provider_authority": PROVIDER_AUTHORITY_FIX_342,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_342,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_342,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_342,
        "local_multi_cloud_proof_executable": LOCAL_MULTI_CLOUD_PROOF_EXECUTABLE_FIX_342,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_342,
        "success_criteria": success,
        "composed_from_workstream_d1_and_execution_track_4": True,
        "sections": sections,
        "sources": {
            "execution_track_4_deployment": True,
            "workstream_d1_phase2_expansion": True,
            "fix_316_operations": True,
            "fix_324_portfolio": True,
            "fix_329_operating_review": True,
            "fix_330_executive_dashboard": True,
        },
        "fix_342_certification_requirements": list(FIX_342_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Multi-cloud operational proof program complete"
        if success.get("program_complete")
        else "Multi-cloud operational proof composed — executions and human review pending"
    )
    return MultiCloudOperationalProofProgramResult(
        ok=True,
        session_id=sid,
        multi_cloud_operational_proof_program=board,
        blockers=blockers,
        detail=detail,
    )
