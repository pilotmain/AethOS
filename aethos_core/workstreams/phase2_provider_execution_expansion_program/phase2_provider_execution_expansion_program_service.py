# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_D1 / FIX 341 — compose Phase 2 provider execution expansion."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_341_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.phase2_provider_execution_expansion_program.phase2_provider_execution_expansion_program_contract import (
    AUTHORITY_EXPANSION_FIX_341,
    CORE_PRINCIPLE,
    FORBIDDEN_EXPANSION_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_341,
    GOVERNANCE_MUTATION_PERFORMED_FIX_341,
    LOCAL_PHASE2_EXECUTION_EXECUTABLE_FIX_341,
    MUTATION_PERFORMED_FIX_341,
    PHASE2_PROVIDER_EXECUTION_EXPANSION_PHASES,
    PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_FIX,
    PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_ID,
    PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_INVARIANT,
    PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_SCHEMA_VERSION,
    PROGRAM_NON_GOALS,
    PROVIDER_SCOPES,
    ROLLBACK_EXECUTION_AUTHORITY_FIX_341,
    SPECIAL_PROVIDER_AUTHORITY_FIX_341,
    TRUST_MUTATION_AUTHORITY_FIX_341,
    WAVE_1_PROVIDER_ORDER,
)
from aethos_core.workstreams.phase2_provider_execution_expansion_program.phase2_provider_execution_expansion_program_executor import (
    assess_provider_readiness,
    build_aws_evidence_bundle,
    build_provider_execution_report,
    build_provider_expansion_registry,
    build_provider_verification_report,
    build_readiness_assessment,
)
from aethos_core.workstreams.phase2_provider_execution_expansion_program.phase2_provider_execution_expansion_program_store import (
    has_phase2_provider_expansion_approve,
    list_phase2_execution_registry_entries,
    list_phase2_provider_execution_expansion_records,
    list_phase2_verification_registry_entries,
)


@dataclass(frozen=True)
class Phase2ProviderExecutionExpansionProgramResult:
    ok: bool
    session_id: str
    phase2_provider_execution_expansion_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_1_provider_expansion_registry(*, session_id: str) -> dict[str, Any]:
    return {"provider_expansion_registry": build_provider_expansion_registry(session_id=session_id)}


def _provider_phase_builder(provider: str):
    def _builder(*, session_id: str) -> dict[str, Any]:
        deployment_key = PROVIDER_SCOPES[provider].get("deployment_report") or f"{provider.lower()}_deployment_report"
        verification_key = PROVIDER_SCOPES[provider].get("verification_report")
        section: dict[str, Any] = {
            deployment_key: build_provider_execution_report(session_id=session_id, provider=provider),
        }
        if verification_key:
            section[verification_key] = build_provider_verification_report(session_id=session_id, provider=provider)
        if provider == "AWS":
            section["aws_evidence_bundle"] = build_aws_evidence_bundle(session_id=session_id)
        section["provider_readiness"] = assess_provider_readiness(provider=provider)
        return section

    return _builder


def _build_phase_6_verification_registry(*, session_id: str) -> dict[str, Any]:
    verifications = [
        row for row in list_phase2_verification_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    return {
        "verification_registry": {
            "registry_id": "phase2-verification-registry",
            "verification_count": len(verifications),
            "verifications": verifications[-10:],
            "read_only": True,
        }
    }


def _build_phase_8_expansion_dashboard(*, session_id: str) -> dict[str, Any]:
    assessment = build_readiness_assessment(session_id=session_id)
    executions = [
        row for row in list_phase2_execution_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    return {
        "expansion_dashboard": {
            "dashboard_id": "phase2-provider-expansion-dashboard",
            "wave_1_providers": list(WAVE_1_PROVIDER_ORDER),
            "expansion_approved": has_phase2_provider_expansion_approve(session_id=session_id),
            "execution_count": len(executions),
            "ready_count": assessment.get("ready_count"),
            "multi_cloud_ready": assessment.get("multi_cloud_ready"),
            "authority_expansion": False,
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, session_id: str) -> dict[str, Any]:
    records = _session_records(list_phase2_provider_execution_expansion_records(), session_id=session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "phase2_provider_expansion_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("phase2_provider_expansion_review_")]
    reviews = [r for r in records if str(r.get("kind") or "").endswith("_review_note")]

    return {
        "phase2_provider_expansion_review_registry": {
            "registry_id": "phase2-provider-expansion-review-registry",
            "note_count": len(notes),
            "review_count": len(reviews),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "reviews": reviews[-10:],
            "decisions": decisions[-5:],
            "read_only": True,
        }
    }


def _success_criteria(*, session_id: str) -> dict[str, Any]:
    assessment = build_readiness_assessment(session_id=session_id)
    executions = [
        row for row in list_phase2_execution_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    return {
        "phase2_providers_executable": has_phase2_provider_expansion_approve(session_id=session_id),
        "aws_scope_supported": True,
        "kubernetes_scope_supported": True,
        "azure_scope_supported": True,
        "gcp_scope_supported": True,
        "multi_cloud_execution_demonstrated": len(executions) >= 1,
        "governance_inherited": True,
        "authority_expansion_performed": False,
        "program_complete": (
            has_phase2_provider_expansion_approve(session_id=session_id)
            and len(executions) >= 1
            and assessment.get("multi_cloud_ready") is not False
        ),
    }


def build_phase2_provider_execution_expansion_program(
    *, session_id: str = "default"
) -> Phase2ProviderExecutionExpansionProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {}
    phase_builders = (
        _build_phase_1_provider_expansion_registry,
        _provider_phase_builder("AWS"),
        _provider_phase_builder("Kubernetes"),
        _provider_phase_builder("Azure"),
        _provider_phase_builder("GCP"),
        _build_phase_6_verification_registry,
        lambda session_id=sid: {"readiness_assessment": build_readiness_assessment(session_id=session_id)},
        _build_phase_8_expansion_dashboard,
        _build_phase_9_human_review,
    )
    for phase, builder in zip(PHASE2_PROVIDER_EXECUTION_EXPANSION_PHASES, phase_builders, strict=True):
        sections[phase] = [builder(session_id=sid)]

    success = _success_criteria(session_id=sid)
    if not has_phase2_provider_expansion_approve(session_id=sid):
        blockers.append("phase2_provider_expansion_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_SCHEMA_VERSION,
        "workstream_id": PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_ID,
        "fix_id": PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_341,
        "execution_performed": len(
            [row for row in list_phase2_execution_registry_entries() if str(row.get("session_id") or "") == sid]
        )
        > 0,
        "core_principle": CORE_PRINCIPLE,
        "invariant": PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_EXPANSION_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(PHASE2_PROVIDER_EXECUTION_EXPANSION_PHASES),
        "wave_1_provider_order": list(WAVE_1_PROVIDER_ORDER),
        "provider_scopes": {k: v["services"] for k, v in PROVIDER_SCOPES.items()},
        "authority_expansion": AUTHORITY_EXPANSION_FIX_341,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_341,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_341,
        "special_provider_authority": SPECIAL_PROVIDER_AUTHORITY_FIX_341,
        "rollback_execution_authority": ROLLBACK_EXECUTION_AUTHORITY_FIX_341,
        "local_phase2_execution_executable": LOCAL_PHASE2_EXECUTION_EXECUTABLE_FIX_341,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_341,
        "success_criteria": success,
        "composed_from_execution_track_4_and_workstream_d1": True,
        "sections": sections,
        "sources": {
            "execution_track_4_deployment": True,
            "workstream_c1_operational_proof": True,
        },
        "fix_341_certification_requirements": list(FIX_341_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Phase 2 provider execution expansion complete"
        if success.get("program_complete")
        else "Phase 2 provider expansion composed — human approval and executions pending"
    )
    return Phase2ProviderExecutionExpansionProgramResult(
        ok=True,
        session_id=sid,
        phase2_provider_execution_expansion_program=board,
        blockers=blockers,
        detail=detail,
    )
