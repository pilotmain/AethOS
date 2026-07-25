# SPDX-License-Identifier: Apache-2.0
"""Governed mutation preflight approval from Mission Control approval inbox."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.mission_control.approval_inbox.approval_audit_service import persist_ui_approval_audit
from aethos_core.mission_control.approval_inbox.approval_inbox_service import build_approval_inbox


@dataclass(frozen=True)
class MutationApprovalExecutionResult:
    ok: bool
    session_id: str
    inbox_id: str
    preflight_job_id: str = ""
    execution_job_id: str = ""
    audit_id: str = ""
    detail: str = ""
    blockers: list[str] = field(default_factory=list)
    replay_protected: bool = False


def _find_mutation_inbox_item(*, session_id: str, inbox_id: str) -> dict[str, Any] | None:
    inbox = build_approval_inbox(session_id=session_id)
    if not inbox.ok:
        return None
    for item in inbox.items:
        if str(item.get("inbox_id") or "") != inbox_id:
            continue
        if str(item.get("lane") or "") != "governed_execution":
            continue
        if not item.get("mutation_inbox_execution_enabled"):
            continue
        return item
    return None


def _preflight_job_id_from_item(item: dict[str, Any]) -> str:
    ctx = item.get("context") if isinstance(item.get("context"), dict) else {}
    job_id = str(ctx.get("job_id") or "")
    if job_id:
        return job_id
    inbox_id = str(item.get("inbox_id") or "")
    if inbox_id.startswith("job-"):
        return inbox_id[4:]
    return ""


def execute_mutation_preflight_from_inbox(*, session_id: str, inbox_id: str) -> MutationApprovalExecutionResult:
    from aethos_core.mission_control.approval_inbox.approval_audit_service import find_replay_audit
    from aethos_core.operations.mutations.mutation_execution_flow import (
        MutationExecutionError,
        approve_mutation_execution,
    )

    prior = find_replay_audit(session_id=session_id, inbox_id=inbox_id)
    if prior and str(prior.get("outcome") or "") == "success":
        return MutationApprovalExecutionResult(
            ok=True,
            session_id=session_id,
            inbox_id=inbox_id,
            preflight_job_id=str(prior.get("preflight_job_id") or ""),
            execution_job_id=str(prior.get("execution_job_id") or ""),
            audit_id=str(prior.get("approval_id") or ""),
            detail="Duplicate UI approval suppressed — prior successful audit exists.",
            replay_protected=True,
        )

    item = _find_mutation_inbox_item(session_id=session_id, inbox_id=inbox_id)
    if not item:
        return MutationApprovalExecutionResult(
            ok=False,
            session_id=session_id,
            inbox_id=inbox_id,
            blockers=["inbox_item_not_found"],
            detail="Mutation preflight item not found.",
        )

    preflight_job_id = _preflight_job_id_from_item(item)
    if not preflight_job_id:
        return MutationApprovalExecutionResult(
            ok=False,
            session_id=session_id,
            inbox_id=inbox_id,
            blockers=["preflight_job_id_missing"],
            detail="Mutation preflight job id missing from inbox item.",
        )

    try:
        preflight, execution = approve_mutation_execution(preflight_job_id)
    except MutationExecutionError as exc:
        audit = persist_ui_approval_audit(
            {
                "session_id": session_id,
                "inbox_id": inbox_id,
                "lane": "governed_execution",
                "gate_id": str(item.get("gate_id") or "mutation_preflight"),
                "outcome": "failed",
                "gate_satisfied": False,
                "preflight_job_id": preflight_job_id,
                "blockers": [str(exc)],
                "failure_reason": str(exc),
            }
        )
        return MutationApprovalExecutionResult(
            ok=False,
            session_id=session_id,
            inbox_id=inbox_id,
            preflight_job_id=preflight_job_id,
            audit_id=str(audit.get("approval_id") or ""),
            detail=str(exc),
            blockers=[str(exc)],
        )

    execution_job_id = str(getattr(execution, "id", "") or "")
    audit = persist_ui_approval_audit(
        {
            "session_id": session_id,
            "inbox_id": inbox_id,
            "lane": "governed_execution",
            "gate_id": str(item.get("gate_id") or "mutation_preflight"),
            "outcome": "success",
            "gate_satisfied": True,
            "mutation_performed": True,
            "direct_provider_mutation": False,
            "preflight_job_id": preflight_job_id,
            "execution_job_id": execution_job_id,
            "reply_excerpt": f"Approved mutation preflight {preflight_job_id}; execution job {execution_job_id} enqueued.",
        }
    )

    return MutationApprovalExecutionResult(
        ok=True,
        session_id=session_id,
        inbox_id=inbox_id,
        preflight_job_id=preflight_job_id,
        execution_job_id=execution_job_id,
        audit_id=str(audit.get("approval_id") or ""),
        detail="Mutation approved — governed execution job enqueued.",
    )
