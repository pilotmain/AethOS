# SPDX-License-Identifier: Apache-2.0
"""FIX 336 / EXECUTION_TRACK_3 — compose governed Git delivery track."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_store import (
    list_changeset_registry_entries,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_contract import (
    CLOUD_PROVISIONING_AUTHORITY_FIX_336,
    CORE_PRINCIPLE,
    DELIVERY_BRANCH_PREFIX,
    DEPLOYMENT_AUTHORITY_FIX_336,
    EXECUTION_PERFORMED_FIX_336,
    EXECUTION_TRACK_3_ID,
    EXECUTION_TRACK_3_PHASES,
    FORBIDDEN_GIT_DELIVERY_ACTIONS,
    GIT_DELIVERY_AUTHORITY_FIX_336,
    GOVERNED_GIT_DELIVERY_FIX,
    GOVERNED_GIT_DELIVERY_INVARIANT,
    GOVERNED_GIT_DELIVERY_PRINCIPLES,
    GOVERNED_GIT_DELIVERY_SCHEMA_VERSION,
    GOVERNANCE_MUTATION_PERFORMED_FIX_336,
    LOCAL_GIT_DELIVERY_EXECUTABLE_FIX_336,
    MERGE_AUTHORITY_FIX_336,
    MUTATION_PERFORMED_FIX_336,
    REQUIRED_DELIVERY_REVIEW_KINDS,
    ROLLBACK_AUTHORITY_FIX_336,
    TRACK_NON_GOALS,
    TRUST_MUTATION_AUTHORITY_FIX_336,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_executor import (
    verify_git_delivery,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_store import (
    all_delivery_reviews_recorded,
    has_git_delivery_decision_approve,
    has_git_delivery_executed,
    latest_record_by_kind,
    list_delivery_registry_entries,
    list_governed_git_delivery_records,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_store import (
    list_workspace_registry_entries,
)
from aethos_core.governance.governance_friction_approval_contract import FIX_336_CERTIFICATION_REQUIREMENTS


@dataclass(frozen=True)
class GovernedGitDeliveryResult:
    ok: bool
    session_id: str
    governed_git_delivery: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _latest_changeset(*, session_id: str) -> dict[str, Any]:
    entries = [
        row for row in list_changeset_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    return entries[-1] if entries else {}


def _build_phase_1_delivery_request_intake(*, session_id: str) -> dict[str, Any]:
    records = _session_records(list_governed_git_delivery_records(), session_id=session_id)
    requests = [r for r in records if str(r.get("kind") or "") == "git_delivery_review_note"]
    changeset = _latest_changeset(session_id=session_id)
    workspaces = [
        row for row in list_workspace_registry_entries() if str(row.get("session_id") or "") == session_id
    ]

    git_delivery_request_registry = {
        "registry_id": "git-delivery-request-registry",
        "request_count": len(requests),
        "requests": requests[-10:],
        "approved_workspace_present": bool(workspaces),
        "approved_changeset_present": bool(changeset),
        "read_only": True,
    }

    git_delivery_scope_report = {
        "report_id": "git-delivery-scope-report",
        "changeset_id": changeset.get("changeset_id"),
        "workspace_id": (workspaces[-1].get("workspace_id") if workspaces else None),
        "file_count": len((changeset.get("new_files") or []) + (changeset.get("modified_files") or [])),
        "merge_performed": False,
        "read_only": True,
    }

    return {
        "git_delivery_request_registry": git_delivery_request_registry,
        "git_delivery_scope_report": git_delivery_scope_report,
    }


def _build_phase_2_branch_planning(*, session_id: str) -> dict[str, Any]:
    intake = latest_record_by_kind(session_id=session_id, kind="git_delivery_review_note")
    metadata = dict((intake or {}).get("metadata") or {})
    changeset = _latest_changeset(session_id=session_id)
    work_item = metadata.get("work_item") or metadata.get("feature") or changeset.get("plan_id") or "work-item"
    target_branch = metadata.get("target_branch") or metadata.get("base_branch") or "main"
    branch_pattern = f"{DELIVERY_BRANCH_PREFIX}/<{work_item}>/<timestamp>"

    branch_plan_report = {
        "report_id": "branch-plan-report",
        "repository": metadata.get("repository") or metadata.get("repo"),
        "target_branch": target_branch,
        "delivery_branch_pattern": branch_pattern,
        "work_item": work_item,
        "read_only": True,
    }

    deliveries = [
        row for row in list_delivery_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    delivery_branch_registry = {
        "registry_id": "delivery-branch-registry",
        "entry_count": len(deliveries),
        "branches": [
            {
                "delivery_branch": row.get("delivery_branch"),
                "target_branch": row.get("target_branch"),
                "delivery_id": row.get("delivery_id"),
            }
            for row in deliveries[-5:]
        ],
        "read_only": True,
    }

    return {
        "branch_plan_report": branch_plan_report,
        "delivery_branch_registry": delivery_branch_registry,
    }


def _build_phase_3_commit_assembly(*, session_id: str) -> dict[str, Any]:
    changeset = _latest_changeset(session_id=session_id)
    files = (changeset.get("new_files") or []) + (changeset.get("modified_files") or [])

    commit_package_report = {
        "report_id": "commit-package-report",
        "generated_code_files": [f for f in files if not str(f).startswith("docs/") and "test" not in str(f).lower()],
        "generated_test_files": changeset.get("generated_tests") or [],
        "generated_documentation_files": changeset.get("generated_documentation") or [],
        "metadata_files": [f for f in files if "governance" in str(f).lower() or "aethos" in str(f).lower()],
        "read_only": True,
    }

    commit_evidence_bundle = {
        "bundle_id": "commit-evidence-bundle",
        "changeset_id": changeset.get("changeset_id"),
        "files": files,
        "review_gates": list(REQUIRED_DELIVERY_REVIEW_KINDS),
        "read_only": True,
    }

    return {
        "commit_package_report": commit_package_report,
        "commit_evidence_bundle": commit_evidence_bundle,
    }


def _build_phase_4_commit_creation(*, session_id: str) -> dict[str, Any]:
    deliveries = [
        row for row in list_delivery_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    latest = deliveries[-1] if deliveries else {}

    commit_creation_report = {
        "report_id": "commit-creation-report",
        "commit_hash": latest.get("commit_hash"),
        "changed_files": latest.get("changed_files") or [],
        "delivery_executed": has_git_delivery_executed(session_id=session_id),
        "merge_performed": False,
        "read_only": True,
    }
    return {"commit_creation_report": commit_creation_report}


def _build_phase_5_push_delivery(*, session_id: str) -> dict[str, Any]:
    deliveries = [
        row for row in list_delivery_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    latest = deliveries[-1] if deliveries else {}
    push = latest.get("push_receipt") or {}

    push_delivery_report = {
        "report_id": "push-delivery-report",
        "branch": latest.get("delivery_branch") or push.get("branch"),
        "remote_branch_ref": push.get("remote_branch_ref"),
        "push_ok": push.get("ok"),
        "push_simulated": push.get("simulated"),
        "delivery_executed": has_git_delivery_executed(session_id=session_id),
        "read_only": True,
    }
    return {"push_delivery_report": push_delivery_report}


def _build_phase_6_pull_request_creation(*, session_id: str) -> dict[str, Any]:
    deliveries = [
        row for row in list_delivery_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    latest = deliveries[-1] if deliveries else {}
    pr = latest.get("pull_request_receipt") or {}

    pull_request_report = {
        "report_id": "pull-request-report",
        "pull_request_url": pr.get("pull_request_url"),
        "pull_request_number": pr.get("pull_request_number"),
        "title": pr.get("title"),
        "base_branch": pr.get("base_branch") or latest.get("target_branch"),
        "head_branch": pr.get("head_branch") or latest.get("delivery_branch"),
        "pr_simulated": pr.get("simulated"),
        "merge_performed": False,
        "read_only": True,
    }
    return {"pull_request_report": pull_request_report}


def _build_phase_7_delivery_verification(*, session_id: str) -> dict[str, Any]:
    verification = verify_git_delivery(session_id=session_id)
    git_delivery_verification_report = {
        "report_id": "git-delivery-verification-report",
        **verification,
        "read_only": True,
    }
    return {"git_delivery_verification_report": git_delivery_verification_report}


def _build_phase_8_evidence_collection(*, session_id: str) -> dict[str, Any]:
    records = _session_records(list_governed_git_delivery_records(), session_id=session_id)
    deliveries = [
        row for row in list_delivery_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    latest = deliveries[-1] if deliveries else {}
    verification = verify_git_delivery(session_id=session_id)

    git_delivery_evidence_bundle = {
        "bundle_id": "git-delivery-evidence-bundle",
        "branch_receipt": {
            "delivery_branch": latest.get("delivery_branch"),
            "target_branch": latest.get("target_branch"),
        },
        "commit_receipt": {"commit_hash": latest.get("commit_hash"), "changed_files": latest.get("changed_files")},
        "push_receipt": latest.get("push_receipt"),
        "pull_request_receipt": latest.get("pull_request_receipt"),
        "review_records": records[-10:],
        "verification_receipt": verification,
        "evidence_complete": verification.get("verified") is True,
        "read_only": True,
    }
    return {"git_delivery_evidence_bundle": git_delivery_evidence_bundle}


def _build_phase_9_delivery_dashboard(*, session_id: str) -> dict[str, Any]:
    phase_7 = _build_phase_7_delivery_verification(session_id=session_id)
    verification = phase_7["git_delivery_verification_report"]
    deliveries = [
        row for row in list_delivery_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    latest = deliveries[-1] if deliveries else {}

    git_delivery_dashboard = {
        "dashboard_id": "git-delivery-dashboard",
        "branch_status": "CREATED" if latest.get("delivery_branch") else "PENDING",
        "commit_status": "CREATED" if latest.get("commit_hash") else "PENDING",
        "push_status": "DELIVERED" if (latest.get("push_receipt") or {}).get("ok") else "PENDING",
        "pull_request_status": "CREATED" if (latest.get("pull_request_receipt") or {}).get("pull_request_url") else "PENDING",
        "verification_status": "VERIFIED" if verification.get("verified") else "PENDING",
        "review_status": latest.get("review_status", "PENDING"),
        "git_delivery_decision_approve": has_git_delivery_decision_approve(session_id=session_id),
        "delivery_reviews_complete": all_delivery_reviews_recorded(session_id=session_id),
        "handoff_ready": verification.get("verified") is True,
        "merge_authority": False,
        "read_only": True,
    }
    return {"git_delivery_dashboard": git_delivery_dashboard}


def _success_criteria(*, session_id: str) -> dict[str, Any]:
    verification = verify_git_delivery(session_id=session_id)
    approved = has_git_delivery_decision_approve(session_id=session_id)
    delivered = has_git_delivery_executed(session_id=session_id)
    return {
        "branch_created": delivered,
        "commit_created": delivered,
        "branch_pushed": delivered,
        "pull_request_created": delivered,
        "delivery_evidence_collected": delivered,
        "readiness_validated": verification.get("verified") is True,
        "governance_controls_respected": True,
        "track_complete": approved and delivered and verification.get("verified") is True,
    }


def build_governed_git_delivery(*, session_id: str = "default") -> GovernedGitDeliveryResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {}
    phase_builders = (
        _build_phase_1_delivery_request_intake,
        _build_phase_2_branch_planning,
        _build_phase_3_commit_assembly,
        _build_phase_4_commit_creation,
        _build_phase_5_push_delivery,
        _build_phase_6_pull_request_creation,
        _build_phase_7_delivery_verification,
        _build_phase_8_evidence_collection,
        _build_phase_9_delivery_dashboard,
    )
    for phase, builder in zip(EXECUTION_TRACK_3_PHASES, phase_builders, strict=True):
        sections[phase] = [builder(session_id=sid)]

    success = _success_criteria(session_id=sid)
    if not all_delivery_reviews_recorded(session_id=sid):
        blockers.append("delivery_review_gates_incomplete")
    if not has_git_delivery_decision_approve(session_id=sid):
        blockers.append("git_delivery_decision_approve_required")
    if not has_git_delivery_executed(session_id=sid):
        blockers.append("git_delivery_pending")

    board: dict[str, Any] = {
        "schema_version": GOVERNED_GIT_DELIVERY_SCHEMA_VERSION,
        "execution_track_id": EXECUTION_TRACK_3_ID,
        "fix_id": GOVERNED_GIT_DELIVERY_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_336,
        "execution_performed": has_git_delivery_executed(session_id=sid),
        "core_principle": CORE_PRINCIPLE,
        "invariant": GOVERNED_GIT_DELIVERY_INVARIANT,
        "principles": [f"{key}: {value}" for key, value in GOVERNED_GIT_DELIVERY_PRINCIPLES],
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_GIT_DELIVERY_ACTIONS],
        "non_goals": list(TRACK_NON_GOALS),
        "phases": list(EXECUTION_TRACK_3_PHASES),
        "git_delivery_authority": GIT_DELIVERY_AUTHORITY_FIX_336,
        "merge_authority": MERGE_AUTHORITY_FIX_336,
        "deployment_authority": DEPLOYMENT_AUTHORITY_FIX_336,
        "rollback_authority": ROLLBACK_AUTHORITY_FIX_336,
        "cloud_provisioning_authority": CLOUD_PROVISIONING_AUTHORITY_FIX_336,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_336,
        "local_git_delivery_executable": LOCAL_GIT_DELIVERY_EXECUTABLE_FIX_336,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_336,
        "execution_performed_default": EXECUTION_PERFORMED_FIX_336,
        "success_criteria": success,
        "composed_from_execution_track_1": True,
        "composed_from_execution_track_2": True,
        "sections": sections,
        "sources": {
            "execution_track_1_workspace": True,
            "execution_track_2_changeset": True,
        },
        "fix_336_certification_requirements": list(FIX_336_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Governed Git delivery track complete"
        if success.get("track_complete")
        else "Governed Git delivery track composed — delivery pending human approval"
    )
    return GovernedGitDeliveryResult(
        ok=True,
        session_id=sid,
        governed_git_delivery=board,
        blockers=blockers,
        detail=detail,
    )
