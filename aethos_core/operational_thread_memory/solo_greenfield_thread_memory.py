# SPDX-License-Identifier: Apache-2.0
"""Operational thread memory for solo Railway greenfield deployments."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from aethos_core.operational_thread_memory.thread_persistence import _expires_at, get_active_thread, save_thread_state
from aethos_core.operational_thread_memory.thread_state import OperationalThreadState


def sync_thread_from_solo_greenfield(
    *,
    session_id: str,
    user_text: str,
    plan: dict[str, Any],
    journal: dict[str, Any],
    execution_status: str,
) -> OperationalThreadState:
    """Persist deploy context so status follow-ups stay on Railway, not unrelated routers."""
    deployment_id = str(journal.get("railway_deployment_id") or "")
    service_id = str(journal.get("railway_service_id") or "")
    verification = journal.get("runtime_verification") if isinstance(journal.get("runtime_verification"), dict) else {}
    health_ok = bool(verification.get("verified") or verification.get("ok"))
    deploy_status = str((journal.get("deploy_trigger_metadata") or {}).get("deployment_status") or "").upper()
    if not health_ok and deploy_status == "SUCCESS":
        health_ok = True

    if execution_status == "completed":
        status = "deploy_live"
        last_result = "Railway greenfield deployment completed."
        next_check = "Ask for a status update to poll the latest Railway deployment."
    else:
        status = "deploy_failed"
        last_result = "Railway greenfield deployment did not complete."
        next_check = "Retry the greenfield deploy request or inspect the execution journal."

    state = OperationalThreadState(
        session_id=(session_id or "default").strip(),
        active_thread="railway_greenfield_deployment",
        provider="railway",
        project=plan.get("project") or journal.get("project"),
        environment=plan.get("environment") or journal.get("environment") or "production",
        service=str(plan.get("service_name") or journal.get("service_name") or ""),
        operation="greenfield_deploy",
        status=status,
        last_user_intent=user_text,
        last_system_result=last_result,
        next_check=next_check,
        last_evidence={
            "deployment_id": deployment_id,
            "service_id": service_id,
            "execution_id": journal.get("execution_id"),
            "health_verified": health_ok,
            "repository": plan.get("repo") or journal.get("repo"),
            "branch": plan.get("branch") or journal.get("branch"),
            "deployment_url": journal.get("deployment_url") or journal.get("railway_deployment_url"),
        },
        updated_at=datetime.now(UTC).isoformat(),
        expires_at=_expires_at(),
    )
    save_thread_state(state)
    from aethos_core.continuity_intelligence.operational_focus_model import record_from_thread

    record_from_thread(state)
    return state


def resolve_greenfield_deployment_thread(*, session_id: str) -> OperationalThreadState | None:
    thread = get_active_thread(session_id=session_id)
    if thread is not None and thread.active_thread == "railway_greenfield_deployment":
        return thread

    from aethos_core.providers.railway.execution_contract.execution_journal import load_latest_journal_for_session

    journal = load_latest_journal_for_session(session_id=session_id)
    if not journal or not journal.get("railway_service_id"):
        return None

    plan = {
        "project": journal.get("project"),
        "environment": journal.get("environment"),
        "service_name": journal.get("service_name"),
        "repo": journal.get("repo"),
        "branch": journal.get("branch"),
    }
    execution_status = "completed" if journal.get("runtime_verification_performed") else "failed"
    return sync_thread_from_solo_greenfield(
        session_id=session_id,
        user_text=str(journal.get("last_user_intent") or "Deploy AethOS to Railway"),
        plan=plan,
        journal=journal,
        execution_status=execution_status,
    )


def poll_greenfield_deployment_status(*, thread: OperationalThreadState) -> dict[str, Any]:
    evidence = dict(thread.last_evidence or {})
    service_id = str(evidence.get("service_id") or "")
    deployment_id = str(evidence.get("deployment_id") or "")
    if not service_id:
        return {"ok": False, "detail": "No Railway service id stored for this deployment thread."}

    from aethos_core.providers.railway.api_client import list_service_deployments
    from aethos_core.providers.railway.credential_truth import resolve_railway_credential

    resolution = resolve_railway_credential()
    token = resolution.token
    if not token:
        return {"ok": False, "detail": "Railway token unavailable — cannot poll deployment status."}

    deployments = list_service_deployments(token, service_id=service_id, limit=5)
    selected = None
    if deployment_id:
        selected = next((row for row in deployments if str(row.get("id") or "") == deployment_id), None)
    if selected is None and deployments:
        selected = deployments[0]

    if selected is None:
        return {"ok": False, "detail": "No Railway deployments returned for the stored service."}

    state = str(selected.get("state") or "unknown").upper()
    health_ok = state in {"SUCCESS", "ACTIVE", "COMPLETED"}
    stored_health = bool(evidence.get("health_verified"))
    return {
        "ok": True,
        "deployment_id": str(selected.get("id") or deployment_id),
        "state": state,
        "health_ok": health_ok or stored_health,
        "url": str(selected.get("url") or evidence.get("deployment_url") or ""),
        "branch": str(selected.get("branch") or evidence.get("branch") or ""),
        "commit": str(selected.get("commit") or ""),
        "error_message": str(selected.get("error_message") or ""),
    }


def compose_greenfield_deployment_status_reply(*, thread: OperationalThreadState) -> tuple[str, str, dict[str, str]]:
    live = poll_greenfield_deployment_status(thread=thread)
    path = thread.service_path()
    evidence = dict(thread.last_evidence or {})

    lines = ["**Railway deployment status**", "", f"- Target: **{path}**"]
    deployment_id = str(live.get("deployment_id") or evidence.get("deployment_id") or "")
    if deployment_id:
        lines.append(f"- Deployment: `{deployment_id}`")
    if live.get("ok"):
        lines.append(f"- State: **{live.get('state')}**")
        lines.append(f"- Health: **{'pass' if live.get('health_ok') else 'pending'}**")
        if live.get("branch"):
            lines.append(f"- Branch: `{live.get('branch')}`")
        if live.get("commit"):
            lines.append(f"- Commit: `{live.get('commit')}`")
        url = str(live.get("url") or "")
        if url:
            lines.append(f"- URL: {url}")
        if live.get("error_message"):
            lines.append(f"- Provider note: {live.get('error_message')}")
    else:
        lines.append(f"- Stored status: **{thread.status.replace('_', ' ')}**")
        lines.append(f"- Live poll: {live.get('detail') or 'unavailable'}")

    lines.extend(["", thread.last_system_result or "Deployment thread is active for this session."])
    meta = {
        "provider": "railway",
        "route_id": "railway_greenfield_deployment_status_followup",
        "deployment_id": deployment_id,
        "service": str(thread.service or ""),
        "project": str(thread.project or ""),
        "environment": str(thread.environment or ""),
        "status": str(live.get("state") or thread.status),
    }
    return "\n".join(lines), "railway_greenfield_deployment_status_followup", meta
