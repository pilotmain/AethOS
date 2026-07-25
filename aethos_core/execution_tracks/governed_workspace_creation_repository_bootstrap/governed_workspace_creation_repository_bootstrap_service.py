# SPDX-License-Identifier: Apache-2.0
"""FIX 334 / EXECUTION_TRACK_1 — compose governed workspace creation track."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_contract import (
    CLOUD_PROVISIONING_AUTHORITY_FIX_334,
    CODE_GENERATION_AUTHORITY_FIX_334,
    CORE_PRINCIPLE,
    DEPLOYMENT_AUTHORITY_FIX_334,
    EXECUTION_PERFORMED_FIX_334,
    EXECUTION_TRACK_1_ID,
    EXECUTION_TRACK_1_PHASES,
    FORBIDDEN_WORKSPACE_CREATION_ACTIONS,
    GIT_PUSH_AUTHORITY_FIX_334,
    GOVERNED_WORKSPACE_CREATION_PRINCIPLES,
    GOVERNED_WORKSPACE_CREATION_REPOSITORY_BOOTSTRAP_FIX,
    GOVERNED_WORKSPACE_CREATION_REPOSITORY_BOOTSTRAP_INVARIANT,
    GOVERNED_WORKSPACE_CREATION_REPOSITORY_BOOTSTRAP_SCHEMA_VERSION,
    GOVERNANCE_MUTATION_PERFORMED_FIX_334,
    LOCAL_BOOTSTRAP_EXECUTABLE_FIX_334,
    MUTATION_PERFORMED_FIX_334,
    PR_CREATION_AUTHORITY_FIX_334,
    PROVIDER_MUTATION_AUTHORITY_FIX_334,
    SUPPORTED_REPOSITORY_TEMPLATES,
    TRACK_NON_GOALS,
    TRUST_MUTATION_AUTHORITY_FIX_334,
    WORKSPACE_CREATION_AUTHORITY_FIX_334,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_executor import (
    verify_workspace_bootstrap,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_store import (
    has_workspace_bootstrap_executed,
    has_workspace_decision_approve,
    list_governed_workspace_creation_records,
    list_workspace_registry_entries,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_templates import (
    list_project_templates,
)
from aethos_core.governance.governance_friction_approval_contract import FIX_334_CERTIFICATION_REQUIREMENTS


@dataclass(frozen=True)
class GovernedWorkspaceCreationRepositoryBootstrapResult:
    ok: bool
    session_id: str
    governed_workspace_creation_repository_bootstrap: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_1_workspace_registry(*, session_id: str) -> dict[str, Any]:
    registry_entries = [
        row for row in list_workspace_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    records = _session_records(list_governed_workspace_creation_records(), session_id=session_id)
    creation_notes = [r for r in records if str(r.get("kind") or "") == "workspace_creation_review_note"]

    workspace_registry = {
        "registry_id": "workspace-registry",
        "entry_count": len(registry_entries),
        "entries": registry_entries,
        "pending_creation_reviews": creation_notes[-5:],
        "tracks": ["local_workspace_path", "project_ownership", "tenant_ownership", "repository_association"],
        "read_only": True,
    }

    healthy = sum(1 for row in registry_entries if str(row.get("health_state") or "") == "bootstrapped")
    workspace_health_report = {
        "report_id": "workspace-health-report",
        "workspace_count": len(registry_entries),
        "healthy_count": healthy,
        "pending_count": max(0, len(creation_notes) - len(registry_entries)),
        "health_state": "HEALTHY" if registry_entries and healthy == len(registry_entries) else "PENDING",
        "deployment_performed": False,
        "read_only": True,
    }

    workspace_evidence_registry = {
        "registry_id": "workspace-evidence-registry",
        "creation_review_count": len(creation_notes),
        "registry_entry_count": len(registry_entries),
        "recent_records": records[-10:],
        "read_only": True,
    }

    return {
        "workspace_registry": workspace_registry,
        "workspace_health_report": workspace_health_report,
        "workspace_evidence_registry": workspace_evidence_registry,
    }


def _build_phase_2_repository_bootstrap(*, session_id: str) -> dict[str, Any]:
    records = _session_records(list_governed_workspace_creation_records(), session_id=session_id)
    bootstrap_notes = [r for r in records if str(r.get("kind") or "") == "workspace_bootstrap_review_note"]
    executed = [r for r in records if str(r.get("kind") or "") == "workspace_bootstrap_executed_note"]
    approved = has_workspace_decision_approve(session_id=session_id)
    bootstrapped = has_workspace_bootstrap_executed(session_id=session_id)

    repository_bootstrap_report = {
        "report_id": "repository-bootstrap-report",
        "workspace_decision_approve": approved,
        "bootstrap_executed": bootstrapped,
        "bootstrap_review_notes": bootstrap_notes[-5:],
        "execution_receipts": executed[-3:],
        "supported_templates": list(SUPPORTED_REPOSITORY_TEMPLATES),
        "git_push_performed": False,
        "deployment_performed": False,
        "code_generation_performed": False,
        "bootstrap_ready": approved and bool(bootstrap_notes or bootstrapped),
        "read_only": True,
    }
    return {"repository_bootstrap_report": repository_bootstrap_report}


def _build_phase_3_project_template_registry(*, session_id: str) -> dict[str, Any]:
    templates = list_project_templates()
    ready_count = sum(1 for row in templates if row.get("readiness") == "READY")

    project_template_registry = {
        "registry_id": "project-template-registry",
        "template_count": len(templates),
        "templates": templates,
        "approved_templates": list(SUPPORTED_REPOSITORY_TEMPLATES),
        "read_only": True,
    }

    template_readiness_report = {
        "report_id": "template-readiness-report",
        "ready_template_count": ready_count,
        "total_template_count": len(templates),
        "readiness_state": "READY" if ready_count == len(templates) else "PARTIAL",
        "session_id": session_id,
        "read_only": True,
    }

    return {
        "project_template_registry": project_template_registry,
        "template_readiness_report": template_readiness_report,
    }


def _build_phase_4_workspace_verification(*, session_id: str) -> dict[str, Any]:
    verification = verify_workspace_bootstrap(session_id=session_id)
    workspace_verification_report = {
        "report_id": "workspace-verification-report",
        **verification,
        "structure_valid": verification.get("verified") is True,
        "template_valid": verification.get("governance_metadata_valid") is True,
        "repository_healthy": verification.get("ok") is True,
        "read_only": True,
    }
    return {"workspace_verification_report": workspace_verification_report}


def _build_phase_5_bootstrap_evidence(*, session_id: str) -> dict[str, Any]:
    records = _session_records(list_governed_workspace_creation_records(), session_id=session_id)
    decisions = [r for r in records if str(r.get("kind") or "").startswith("workspace_decision_")]
    executions = [r for r in records if str(r.get("kind") or "") == "workspace_bootstrap_executed_note"]
    verification = verify_workspace_bootstrap(session_id=session_id)

    workspace_creation_evidence_bundle = {
        "bundle_id": "workspace-creation-evidence-bundle",
        "creation_events": [r for r in records if "review_note" in str(r.get("kind") or "")][-10:],
        "approval_events": decisions[-5:],
        "verification_receipt": verification,
        "execution_receipts": executions[-3:],
        "evidence_complete": bool(decisions) and verification.get("verified") is True,
        "read_only": True,
    }
    return {"workspace_creation_evidence_bundle": workspace_creation_evidence_bundle}


def _build_phase_6_workspace_dashboard(*, session_id: str) -> dict[str, Any]:
    phase_1 = _build_phase_1_workspace_registry(session_id=session_id)
    phase_2 = _build_phase_2_repository_bootstrap(session_id=session_id)
    phase_3 = _build_phase_3_project_template_registry(session_id=session_id)
    phase_4 = _build_phase_4_workspace_verification(session_id=session_id)
    verification = phase_4["workspace_verification_report"]

    workspace_creation_dashboard = {
        "dashboard_id": "workspace-creation-dashboard",
        "workspace_status": phase_1["workspace_health_report"].get("health_state"),
        "repository_status": "BOOTSTRAPPED"
        if phase_2["repository_bootstrap_report"].get("bootstrap_executed")
        else "PENDING",
        "template_status": phase_3["template_readiness_report"].get("readiness_state"),
        "verification_status": "VERIFIED" if verification.get("verified") else "PENDING",
        "workspace_decision_approve": has_workspace_decision_approve(session_id=session_id),
        "handoff_ready": verification.get("verified") is True,
        "deployment_authority": False,
        "read_only": True,
    }
    return {"workspace_creation_dashboard": workspace_creation_dashboard}


def _success_criteria(*, session_id: str) -> dict[str, Any]:
    verification = verify_workspace_bootstrap(session_id=session_id)
    approved = has_workspace_decision_approve(session_id=session_id)
    bootstrapped = has_workspace_bootstrap_executed(session_id=session_id)
    return {
        "workspace_created": bootstrapped,
        "repository_structure_prepared": bootstrapped,
        "delivery_metadata_initialized": bootstrapped,
        "readiness_validated": verification.get("verified") is True,
        "evidence_produced": approved and bootstrapped,
        "governance_controls_respected": True,
        "track_complete": approved and bootstrapped and verification.get("verified") is True,
    }


def _compose_product_request_context(*, session_id: str) -> dict[str, Any]:
    try:
        from aethos_core.mission_control.governed_application_generation.governed_application_generation_store import (
            generation_decision_status,
            latest_record_by_kind,
        )

        status = generation_decision_status(session_id=session_id)
        prd = latest_record_by_kind(session_id=session_id, kind="prd_intake_note")
        return {
            "composed_from_fix_250": True,
            "generation_decision_status": status,
            "product_request_present": prd is not None,
            "read_only": True,
        }
    except Exception:
        return {"composed_from_fix_250": False, "read_only": True}


def build_governed_workspace_creation_repository_bootstrap(
    *,
    session_id: str = "default",
) -> GovernedWorkspaceCreationRepositoryBootstrapResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {}
    phase_builders = (
        _build_phase_1_workspace_registry,
        _build_phase_2_repository_bootstrap,
        _build_phase_3_project_template_registry,
        _build_phase_4_workspace_verification,
        _build_phase_5_bootstrap_evidence,
        _build_phase_6_workspace_dashboard,
    )
    for phase, builder in zip(EXECUTION_TRACK_1_PHASES, phase_builders, strict=True):
        sections[phase] = [builder(session_id=sid)]

    success = _success_criteria(session_id=sid)
    if not has_workspace_decision_approve(session_id=sid):
        blockers.append("workspace_decision_approve_required")
    if not has_workspace_bootstrap_executed(session_id=sid):
        blockers.append("repository_bootstrap_pending")

    board: dict[str, Any] = {
        "schema_version": GOVERNED_WORKSPACE_CREATION_REPOSITORY_BOOTSTRAP_SCHEMA_VERSION,
        "execution_track_id": EXECUTION_TRACK_1_ID,
        "fix_id": GOVERNED_WORKSPACE_CREATION_REPOSITORY_BOOTSTRAP_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_334,
        "execution_performed": has_workspace_bootstrap_executed(session_id=sid),
        "core_principle": CORE_PRINCIPLE,
        "invariant": GOVERNED_WORKSPACE_CREATION_REPOSITORY_BOOTSTRAP_INVARIANT,
        "principles": [f"{key}: {value}" for key, value in GOVERNED_WORKSPACE_CREATION_PRINCIPLES],
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_WORKSPACE_CREATION_ACTIONS],
        "non_goals": list(TRACK_NON_GOALS),
        "phases": list(EXECUTION_TRACK_1_PHASES),
        "workspace_creation_authority": WORKSPACE_CREATION_AUTHORITY_FIX_334,
        "deployment_authority": DEPLOYMENT_AUTHORITY_FIX_334,
        "git_push_authority": GIT_PUSH_AUTHORITY_FIX_334,
        "pr_creation_authority": PR_CREATION_AUTHORITY_FIX_334,
        "cloud_provisioning_authority": CLOUD_PROVISIONING_AUTHORITY_FIX_334,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_334,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_334,
        "code_generation_authority": CODE_GENERATION_AUTHORITY_FIX_334,
        "local_bootstrap_executable": LOCAL_BOOTSTRAP_EXECUTABLE_FIX_334,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_334,
        "execution_performed_default": EXECUTION_PERFORMED_FIX_334,
        "success_criteria": success,
        "product_request_context": _compose_product_request_context(session_id=sid),
        "sections": sections,
        "sources": {
            "fix_250": True,
            "fix_301": True,
            "local_workspace_registry": True,
        },
        "fix_334_certification_requirements": list(FIX_334_CERTIFICATION_REQUIREMENTS),
    }

    ok = True
    detail = (
        "Governed workspace creation track complete"
        if success.get("track_complete")
        else "Governed workspace creation track composed — bootstrap pending human approval"
    )
    return GovernedWorkspaceCreationRepositoryBootstrapResult(
        ok=ok,
        session_id=sid,
        governed_workspace_creation_repository_bootstrap=board,
        blockers=blockers,
        detail=detail,
    )
