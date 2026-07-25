# SPDX-License-Identifier: Apache-2.0
"""FIX 335 / EXECUTION_TRACK_2 — compose governed code generation track."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_contract import (
    CORE_PRINCIPLE,
    DEPLOYMENT_AUTHORITY_FIX_335,
    EXECUTION_PERFORMED_FIX_335,
    EXECUTION_TRACK_2_ID,
    EXECUTION_TRACK_2_PHASES,
    FORBIDDEN_CODE_GENERATION_ACTIONS,
    GIT_COMMIT_AUTHORITY_FIX_335,
    GIT_PUSH_AUTHORITY_FIX_335,
    GOVERNED_CODE_GENERATION_CHANGESET_CREATION_FIX,
    GOVERNED_CODE_GENERATION_CHANGESET_CREATION_INVARIANT,
    GOVERNED_CODE_GENERATION_CHANGESET_CREATION_SCHEMA_VERSION,
    GOVERNED_CODE_GENERATION_PRINCIPLES,
    GOVERNANCE_MUTATION_PERFORMED_FIX_335,
    LOCAL_CODE_GENERATION_EXECUTABLE_FIX_335,
    MERGE_AUTHORITY_FIX_335,
    MUTATION_PERFORMED_FIX_335,
    PR_CREATION_AUTHORITY_FIX_335,
    PROVIDER_MUTATION_AUTHORITY_FIX_335,
    REPOSITORY_AUTHORITY_FIX_335,
    REQUIREMENT_TYPES,
    SUPPORTED_GENERATION_STACKS,
    TRACK_NON_GOALS,
    TRUST_MUTATION_AUTHORITY_FIX_335,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_executor import (
    verify_code_generation,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_generators import (
    build_generation_plan,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_store import (
    has_code_generation_executed,
    has_generation_decision_approve,
    latest_record_by_kind,
    list_changeset_registry_entries,
    list_governed_code_generation_records,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_store import (
    list_workspace_registry_entries,
)
from aethos_core.governance.governance_friction_approval_contract import FIX_335_CERTIFICATION_REQUIREMENTS


@dataclass(frozen=True)
class GovernedCodeGenerationChangesetCreationResult:
    ok: bool
    session_id: str
    governed_code_generation_changeset_creation: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _latest_request(*, session_id: str) -> dict[str, Any] | None:
    record = latest_record_by_kind(session_id=session_id, kind="generation_request_review_note")
    if record is None:
        return None
    metadata = dict(record.get("metadata") or {})
    workspace_entries = [
        row for row in list_workspace_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    workspace = workspace_entries[-1] if workspace_entries else {}
    return {
        "title": metadata.get("title") or metadata.get("feature_name") or "generated-feature",
        "feature_name": metadata.get("feature_name") or metadata.get("title") or "generated-feature",
        "requirement_type": metadata.get("type") or metadata.get("requirement_type") or "task",
        "stack": metadata.get("stack"),
        "template_id": workspace.get("template_id"),
        "description": record.get("content"),
    }


def _build_phase_1_requirement_intake(*, session_id: str) -> dict[str, Any]:
    records = _session_records(list_governed_code_generation_records(), session_id=session_id)
    requests = [r for r in records if str(r.get("kind") or "") == "generation_request_review_note"]

    generation_request_registry = {
        "registry_id": "generation-request-registry",
        "request_count": len(requests),
        "requests": requests[-10:],
        "requirement_types": list(REQUIREMENT_TYPES),
        "read_only": True,
    }

    latest = _latest_request(session_id=session_id)
    generation_scope_report = {
        "report_id": "generation-scope-report",
        "request_present": latest is not None,
        "requirement_type": (latest or {}).get("requirement_type"),
        "feature_name": (latest or {}).get("feature_name"),
        "stack": (latest or {}).get("stack"),
        "git_commit_performed": False,
        "read_only": True,
    }

    return {
        "generation_request_registry": generation_request_registry,
        "generation_scope_report": generation_scope_report,
    }


def _build_phase_2_generation_planning(*, session_id: str) -> dict[str, Any]:
    request = _latest_request(session_id=session_id)
    plan = build_generation_plan(request=request) if request else {}

    generation_plan_report = {
        "report_id": "generation-plan-report",
        "plan_id": plan.get("plan_id"),
        "files_affected": plan.get("files_affected") or [],
        "modules_affected": plan.get("modules_affected") or [],
        "dependencies_affected": plan.get("dependencies_affected") or [],
        "risk_level": plan.get("risk_level", "UNKNOWN"),
        "read_only": True,
    }

    change_scope_report = {
        "report_id": "change-scope-report",
        "stack": plan.get("stack"),
        "artifact_count": len(plan.get("artifacts") or []),
        "risk_level": plan.get("risk_level", "UNKNOWN"),
        "review_required": True,
        "read_only": True,
    }

    return {
        "generation_plan_report": generation_plan_report,
        "change_scope_report": change_scope_report,
    }


def _build_phase_3_code_generation(*, session_id: str) -> dict[str, Any]:
    request = _latest_request(session_id=session_id)
    plan = build_generation_plan(request=request) if request else {}
    code_artifacts = [a for a in (plan.get("artifacts") or []) if a.get("kind") == "code"]

    generated_file_registry = {
        "registry_id": "generated-file-registry",
        "file_count": len(code_artifacts),
        "files": [{"path": a.get("path"), "action": a.get("action")} for a in code_artifacts],
        "generation_executed": has_code_generation_executed(session_id=session_id),
        "read_only": True,
    }

    generated_artifact_report = {
        "report_id": "generated-artifact-report",
        "stack": plan.get("stack"),
        "supported_stacks": list(SUPPORTED_GENERATION_STACKS),
        "generation_executed": has_code_generation_executed(session_id=session_id),
        "git_commit_performed": False,
        "read_only": True,
    }

    return {
        "generated_file_registry": generated_file_registry,
        "generated_artifact_report": generated_artifact_report,
    }


def _build_phase_4_test_generation(*, session_id: str) -> dict[str, Any]:
    request = _latest_request(session_id=session_id)
    plan = build_generation_plan(request=request) if request else {}
    tests = [a for a in (plan.get("artifacts") or []) if a.get("kind") == "test"]
    changesets = [
        row for row in list_changeset_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    generated_tests = changesets[-1].get("generated_tests") if changesets else []

    generated_test_registry = {
        "registry_id": "generated-test-registry",
        "test_count": len(tests),
        "planned_tests": [{"path": a.get("path")} for a in tests],
        "generated_tests": generated_tests,
        "read_only": True,
    }

    test_generation_report = {
        "report_id": "test-generation-report",
        "unit_tests": [p for p in generated_tests if "test" in str(p)],
        "integration_tests": [],
        "validation_tests": [p for p in generated_tests if "validation" in str(p)],
        "generation_executed": has_code_generation_executed(session_id=session_id),
        "read_only": True,
    }

    return {
        "generated_test_registry": generated_test_registry,
        "test_generation_report": test_generation_report,
    }


def _build_phase_5_documentation_generation(*, session_id: str) -> dict[str, Any]:
    request = _latest_request(session_id=session_id)
    plan = build_generation_plan(request=request) if request else {}
    docs = [a for a in (plan.get("artifacts") or []) if a.get("kind") == "documentation"]

    generated_documentation_report = {
        "report_id": "generated-documentation-report",
        "documentation_count": len(docs),
        "readme_updates": [a.get("path") for a in docs if "readme" in str(a.get("path", "")).lower()],
        "architecture_notes": [a.get("path") for a in docs if "architecture" in str(a.get("path", "")).lower()],
        "implementation_notes": [a.get("path") for a in docs if "implementation" in str(a.get("path", "")).lower()],
        "generation_executed": has_code_generation_executed(session_id=session_id),
        "read_only": True,
    }

    return {"generated_documentation_report": generated_documentation_report}


def _build_phase_6_changeset_assembly(*, session_id: str) -> dict[str, Any]:
    changesets = [
        row for row in list_changeset_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    latest = changesets[-1] if changesets else {}

    changeset_registry = {
        "registry_id": "changeset-registry",
        "entry_count": len(changesets),
        "entries": changesets[-5:],
        "read_only": True,
    }

    changeset_review_package = {
        "package_id": "changeset-review-package",
        "changeset_id": latest.get("changeset_id"),
        "new_files": latest.get("new_files") or [],
        "modified_files": latest.get("modified_files") or [],
        "deleted_files": latest.get("deleted_files") or [],
        "generated_tests": latest.get("generated_tests") or [],
        "generated_documentation": latest.get("generated_documentation") or [],
        "review_status": latest.get("review_status", "PENDING"),
        "git_commit_performed": False,
        "git_push_performed": False,
        "pr_creation_performed": False,
        "read_only": True,
    }

    return {
        "changeset_registry": changeset_registry,
        "changeset_review_package": changeset_review_package,
    }


def _build_phase_7_verification(*, session_id: str) -> dict[str, Any]:
    verification = verify_code_generation(session_id=session_id)
    generation_verification_report = {
        "report_id": "generation-verification-report",
        **verification,
        "read_only": True,
    }
    return {"generation_verification_report": generation_verification_report}


def _build_phase_8_evidence(*, session_id: str) -> dict[str, Any]:
    records = _session_records(list_governed_code_generation_records(), session_id=session_id)
    decisions = [r for r in records if str(r.get("kind") or "").startswith("generation_decision_")]
    executions = [r for r in records if str(r.get("kind") or "") == "code_generation_executed_note"]
    verification = verify_code_generation(session_id=session_id)

    generation_evidence_bundle = {
        "bundle_id": "generation-evidence-bundle",
        "prompts_and_requests": [r for r in records if "review_note" in str(r.get("kind") or "")][-10:],
        "generation_events": executions[-3:],
        "verification_receipt": verification,
        "review_decisions": decisions[-5:],
        "evidence_complete": bool(decisions) and verification.get("verified") is True,
        "read_only": True,
    }
    return {"generation_evidence_bundle": generation_evidence_bundle}


def _build_phase_9_dashboard(*, session_id: str) -> dict[str, Any]:
    phase_1 = _build_phase_1_requirement_intake(session_id=session_id)
    phase_6 = _build_phase_6_changeset_assembly(session_id=session_id)
    phase_7 = _build_phase_7_verification(session_id=session_id)
    verification = phase_7["generation_verification_report"]

    code_generation_dashboard = {
        "dashboard_id": "code-generation-dashboard",
        "request_status": "RECORDED" if phase_1["generation_scope_report"].get("request_present") else "PENDING",
        "generated_file_status": "GENERATED" if has_code_generation_executed(session_id=session_id) else "PENDING",
        "verification_status": "VERIFIED" if verification.get("verified") else "PENDING",
        "review_status": phase_6["changeset_review_package"].get("review_status", "PENDING"),
        "generation_decision_approve": has_generation_decision_approve(session_id=session_id),
        "handoff_ready": verification.get("verified") is True,
        "repository_authority": False,
        "read_only": True,
    }
    return {"code_generation_dashboard": code_generation_dashboard}


def _success_criteria(*, session_id: str) -> dict[str, Any]:
    verification = verify_code_generation(session_id=session_id)
    approved = has_generation_decision_approve(session_id=session_id)
    generated = has_code_generation_executed(session_id=session_id)
    return {
        "files_generated": generated,
        "tests_generated": generated,
        "documentation_generated": generated,
        "changeset_assembled": generated,
        "readiness_validated": verification.get("verified") is True,
        "evidence_produced": approved and generated,
        "governance_controls_respected": True,
        "track_complete": approved and generated and verification.get("verified") is True,
    }


def build_governed_code_generation_changeset_creation(
    *,
    session_id: str = "default",
) -> GovernedCodeGenerationChangesetCreationResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {}
    phase_builders = (
        _build_phase_1_requirement_intake,
        _build_phase_2_generation_planning,
        _build_phase_3_code_generation,
        _build_phase_4_test_generation,
        _build_phase_5_documentation_generation,
        _build_phase_6_changeset_assembly,
        _build_phase_7_verification,
        _build_phase_8_evidence,
        _build_phase_9_dashboard,
    )
    for phase, builder in zip(EXECUTION_TRACK_2_PHASES, phase_builders, strict=True):
        sections[phase] = [builder(session_id=sid)]

    success = _success_criteria(session_id=sid)
    if not has_generation_decision_approve(session_id=sid):
        blockers.append("generation_decision_approve_required")
    if not has_code_generation_executed(session_id=sid):
        blockers.append("code_generation_pending")

    board: dict[str, Any] = {
        "schema_version": GOVERNED_CODE_GENERATION_CHANGESET_CREATION_SCHEMA_VERSION,
        "execution_track_id": EXECUTION_TRACK_2_ID,
        "fix_id": GOVERNED_CODE_GENERATION_CHANGESET_CREATION_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_335,
        "execution_performed": has_code_generation_executed(session_id=sid),
        "core_principle": CORE_PRINCIPLE,
        "invariant": GOVERNED_CODE_GENERATION_CHANGESET_CREATION_INVARIANT,
        "principles": [f"{key}: {value}" for key, value in GOVERNED_CODE_GENERATION_PRINCIPLES],
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_CODE_GENERATION_ACTIONS],
        "non_goals": list(TRACK_NON_GOALS),
        "phases": list(EXECUTION_TRACK_2_PHASES),
        "repository_authority": REPOSITORY_AUTHORITY_FIX_335,
        "git_commit_authority": GIT_COMMIT_AUTHORITY_FIX_335,
        "git_push_authority": GIT_PUSH_AUTHORITY_FIX_335,
        "pr_creation_authority": PR_CREATION_AUTHORITY_FIX_335,
        "merge_authority": MERGE_AUTHORITY_FIX_335,
        "deployment_authority": DEPLOYMENT_AUTHORITY_FIX_335,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_335,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_335,
        "local_code_generation_executable": LOCAL_CODE_GENERATION_EXECUTABLE_FIX_335,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_335,
        "execution_performed_default": EXECUTION_PERFORMED_FIX_335,
        "success_criteria": success,
        "composed_from_execution_track_1": True,
        "sections": sections,
        "sources": {
            "execution_track_1_workspace": True,
            "fix_250_product_context": True,
        },
        "fix_335_certification_requirements": list(FIX_335_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Governed code generation track complete"
        if success.get("track_complete")
        else "Governed code generation track composed — generation pending human approval"
    )
    return GovernedCodeGenerationChangesetCreationResult(
        ok=True,
        session_id=sid,
        governed_code_generation_changeset_creation=board,
        blockers=blockers,
        detail=detail,
    )
