# SPDX-License-Identifier: Apache-2.0
"""Governed operational deployment approval from Mission Control approval inbox."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.mission_control.approval_inbox.approval_audit_service import persist_ui_approval_audit
from aethos_core.mission_control.approval_inbox.approval_inbox_service import build_approval_inbox


@dataclass(frozen=True)
class OperationalDeploymentApprovalExecutionResult:
    ok: bool
    session_id: str
    inbox_id: str
    job_id: str = ""
    preflight_id: str = ""
    orchestration_job_id: str = ""
    audit_id: str = ""
    detail: str = ""
    reply: str = ""
    route_id: str = ""
    blockers: list[str] = field(default_factory=list)
    replay_protected: bool = False


def _find_operational_deployment_inbox_item(*, session_id: str, inbox_id: str) -> dict[str, Any] | None:
    inbox = build_approval_inbox(session_id=session_id)
    if not inbox.ok:
        return None
    for item in inbox.items:
        if str(item.get("inbox_id") or "") != inbox_id:
            continue
        if str(item.get("lane") or "") != "operational_deployment":
            continue
        if not (
            item.get("deployment_inbox_execution_enabled")
            or str(item.get("execution_mode") or "") == "operational_deployment_approve"
        ):
            continue
        return item
    return None


def _job_id_from_item(item: dict[str, Any]) -> str:
    ctx = item.get("context") if isinstance(item.get("context"), dict) else {}
    job_id = str(ctx.get("job_id") or "")
    if job_id:
        return job_id
    inbox_id = str(item.get("inbox_id") or "")
    if inbox_id.startswith("job-"):
        return inbox_id[4:]
    return ""


def _approval_session_id(*, item: dict[str, Any], panel_session_id: str) -> str:
    from aethos_core.runtime.jobs import job_store

    ctx = item.get("context") if isinstance(item.get("context"), dict) else {}
    chat_sid = str(ctx.get("chat_session_id") or "").strip()
    job_id = _job_id_from_item(item)
    if job_id:
        job = job_store.get(job_id)
        if job:
            job_sid = str(getattr(job, "session_id", "") or "").strip()
            if job_sid:
                return job_sid
    return chat_sid or panel_session_id


def execute_operational_deployment_approval_from_inbox(
    *,
    session_id: str,
    inbox_id: str,
) -> OperationalDeploymentApprovalExecutionResult:
    from aethos_core.jobs.pending_job_approval_resolution import route_short_approval_turn
    from aethos_core.mission_control.approval_inbox.approval_audit_service import find_replay_audit

    prior = find_replay_audit(session_id=session_id, inbox_id=inbox_id)
    if prior and str(prior.get("outcome") or "") == "success":
        return OperationalDeploymentApprovalExecutionResult(
            ok=True,
            session_id=session_id,
            inbox_id=inbox_id,
            job_id=str(prior.get("job_id") or ""),
            preflight_id=str(prior.get("preflight_id") or ""),
            orchestration_job_id=str(prior.get("orchestration_job_id") or ""),
            audit_id=str(prior.get("approval_id") or ""),
            detail="Duplicate UI approval suppressed — prior successful audit exists.",
            replay_protected=True,
        )

    item = _find_operational_deployment_inbox_item(session_id=session_id, inbox_id=inbox_id)
    if not item:
        return OperationalDeploymentApprovalExecutionResult(
            ok=False,
            session_id=session_id,
            inbox_id=inbox_id,
            blockers=["inbox_item_not_found"],
            detail="Operational deployment approval item not found.",
        )

    job_id = _job_id_from_item(item)
    if not job_id:
        return OperationalDeploymentApprovalExecutionResult(
            ok=False,
            session_id=session_id,
            inbox_id=inbox_id,
            blockers=["job_id_missing"],
            detail="Deployment preflight job id missing from inbox item.",
        )

    if not item.get("deployment_execution_enabled"):
        audit = persist_ui_approval_audit(
            {
                "session_id": session_id,
                "inbox_id": inbox_id,
                "lane": "operational_deployment",
                "gate_id": str(item.get("gate_id") or ""),
                "outcome": "failed",
                "gate_satisfied": False,
                "job_id": job_id,
                "blockers": ["deployment_execution_disabled"],
                "failure_reason": "deployment_execution_disabled",
            }
        )
        return OperationalDeploymentApprovalExecutionResult(
            ok=False,
            session_id=session_id,
            inbox_id=inbox_id,
            job_id=job_id,
            audit_id=str(audit.get("approval_id") or ""),
            detail=str(item.get("deployment_execution_hint") or "Enable Railway greenfield execution to deploy."),
            blockers=["deployment_execution_disabled"],
        )

    approval_session_id = _approval_session_id(item=item, panel_session_id=session_id)
    chat_message = f"approve {job_id}"
    routed = route_short_approval_turn(chat_message, session_id=approval_session_id)
    if not routed:
        audit = persist_ui_approval_audit(
            {
                "session_id": session_id,
                "inbox_id": inbox_id,
                "lane": "operational_deployment",
                "gate_id": str(item.get("gate_id") or ""),
                "outcome": "failed",
                "gate_satisfied": False,
                "job_id": job_id,
                "chat_message": chat_message,
                "blockers": ["chat_route_not_matched"],
                "failure_reason": "chat_route_not_matched",
            }
        )
        return OperationalDeploymentApprovalExecutionResult(
            ok=False,
            session_id=session_id,
            inbox_id=inbox_id,
            job_id=job_id,
            audit_id=str(audit.get("approval_id") or ""),
            detail="Governed chat route did not accept the approval phrase.",
            blockers=["chat_route_not_matched"],
        )

    reply, route_id, meta = routed
    ok = str(route_id or "") == "pending_job_approval_resolved"
    blockers = [] if ok else [str(meta.get("blocker") or "approval_blocked")]
    audit = persist_ui_approval_audit(
        {
            "session_id": session_id,
            "inbox_id": inbox_id,
            "lane": "operational_deployment",
            "gate_id": str(item.get("gate_id") or ""),
            "outcome": "success" if ok else "failed",
            "gate_satisfied": ok,
            "job_id": str(meta.get("job_id") or job_id),
            "preflight_id": str(meta.get("preflight_id") or ""),
            "orchestration_job_id": str(meta.get("orchestration_job_id") or ""),
            "chat_message": chat_message,
            "approval_session_id": approval_session_id,
            "route_id": route_id,
            "mutation_performed": meta.get("mutation_performed") == "true",
            "reply_excerpt": (reply or "")[:500],
            "blockers": blockers,
            "failure_reason": blockers[0] if blockers else "",
        }
    )
    return OperationalDeploymentApprovalExecutionResult(
        ok=ok,
        session_id=session_id,
        inbox_id=inbox_id,
        job_id=str(meta.get("job_id") or job_id),
        preflight_id=str(meta.get("preflight_id") or ""),
        orchestration_job_id=str(meta.get("orchestration_job_id") or ""),
        audit_id=str(audit.get("approval_id") or ""),
        detail=(reply or "").strip()[:800] if not ok else "Deployment approved via governed chat route.",
        reply=reply or "",
        route_id=route_id or "",
        blockers=blockers,
    )


def reject_operational_deployment_approval_from_inbox(
    *,
    session_id: str,
    inbox_id: str,
) -> OperationalDeploymentApprovalExecutionResult:
    from aethos_core.runtime.jobs import job_store

    item = _find_operational_deployment_inbox_item(session_id=session_id, inbox_id=inbox_id)
    if not item:
        return OperationalDeploymentApprovalExecutionResult(
            ok=False,
            session_id=session_id,
            inbox_id=inbox_id,
            blockers=["inbox_item_not_found"],
            detail="Operational deployment approval item not found.",
        )

    job_id = _job_id_from_item(item)
    if not job_id:
        return OperationalDeploymentApprovalExecutionResult(
            ok=False,
            session_id=session_id,
            inbox_id=inbox_id,
            blockers=["job_id_missing"],
            detail="Deployment preflight job id missing from inbox item.",
        )

    job = job_store.get(job_id)
    if not job:
        return OperationalDeploymentApprovalExecutionResult(
            ok=False,
            session_id=session_id,
            inbox_id=inbox_id,
            job_id=job_id,
            blockers=["job_not_found"],
            detail="Pending deployment preflight job no longer exists.",
        )

    params = dict(job.params or {})
    params["approval_required"] = False
    params["approval_rejected"] = True
    params["execution_status"] = "rejected"
    job.params = params

    audit = persist_ui_approval_audit(
        {
            "session_id": session_id,
            "inbox_id": inbox_id,
            "lane": "operational_deployment",
            "gate_id": str(item.get("gate_id") or ""),
            "outcome": "rejected",
            "gate_satisfied": False,
            "job_id": job_id,
            "route_id": "operational_deployment_rejected",
            "mutation_performed": False,
            "failure_reason": "",
        }
    )
    return OperationalDeploymentApprovalExecutionResult(
        ok=True,
        session_id=session_id,
        inbox_id=inbox_id,
        job_id=job_id,
        audit_id=str(audit.get("approval_id") or ""),
        detail="Deployment approval rejected — preflight will not execute.",
        route_id="operational_deployment_rejected",
    )
