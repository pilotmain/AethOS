# SPDX-License-Identifier: Apache-2.0
"""Mutation thread memory — sync operational context from jobs."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from aethos_core.operational_thread_memory.failure_reason_extractor import extract_failure_reason
from aethos_core.operational_thread_memory.thread_persistence import _expires_at, save_thread_state
from aethos_core.operational_thread_memory.thread_state import OperationalThreadState


def sync_thread_from_preflight(*, job: Any, user_request: str | None = None) -> OperationalThreadState:
    params = getattr(job, "params", None) or {}
    target = dict(params.get("target") or {})
    session_id = str(getattr(job, "session_id", None) or "default")
    state = OperationalThreadState(
        session_id=session_id,
        active_thread=f"{params.get('provider', 'railway')}_mutation",
        provider=str(params.get("provider") or "railway"),
        project=target.get("project_name") or params.get("project_name"),
        environment=target.get("environment") or params.get("environment") or "production",
        service=str(params.get("target_name") or target.get("service_name") or ""),
        operation=str(params.get("operation_type") or ""),
        preflight_job_id=str(getattr(job, "id", "") or ""),
        status="preflight_created",
        last_user_intent=user_request or str(params.get("user_request") or ""),
        last_system_result="Governed preflight created — awaiting approval.",
        next_check="Review preflight and approve in Mission Control → Approvals.",
        updated_at=datetime.now(UTC).isoformat(),
        expires_at=_expires_at(),
    )
    save_thread_state(state)
    from aethos_core.continuity_intelligence.operational_focus_model import record_from_thread

    record_from_thread(state)
    return state


def sync_thread_from_execution_job(*, job: Any) -> OperationalThreadState:
    params = getattr(job, "params", None) or {}
    target = dict(params.get("target") or {})
    artifact = dict(params.get("mutation_execution") or {})
    session_id = str(getattr(job, "session_id", None) or "default")
    exec_state = str(params.get("execution_state") or artifact.get("execution_state") or "")
    restart_state = str(
        params.get("restart_verification_state")
        or (params.get("verification_artifact") or {}).get("evidence", {}).get("restart_verification_state")
        or ""
    )
    from aethos_core.operational_thread_memory.thread_persistence import load_thread_state

    existing = load_thread_state(session_id=session_id)
    failure = extract_failure_reason(job)
    status = restart_state or exec_state or (existing.status if existing else "unknown")
    if failure:
        status = "execution_failed" if exec_state == "execution_failed" or params.get("executed") is False else status

    last_result = _summarize_result(params, artifact, failure, restart_state, exec_state)
    next_check = _next_check(status, failure)
    approved_at = str(
        params.get("mutation_execution_approved_at_iso")
        or (params.get("provider_evidence_bundle") or {}).get("approved_at")
        or artifact.get("mutation_execution_approved_at_iso")
        or ""
    ) or None

    state = OperationalThreadState(
        session_id=session_id,
        active_thread=f"{params.get('provider', 'railway')}_mutation",
        provider=str(params.get("provider") or "railway"),
        project=target.get("project_name") or (existing.project if existing else None),
        environment=target.get("environment") or (existing.environment if existing else "production"),
        service=str(params.get("target_name") or target.get("service_name") or (existing.service if existing else "")),
        operation=str(params.get("operation_type") or (existing.operation if existing else "")),
        preflight_job_id=str(params.get("preflight_job_id") or params.get("source_mutation_preflight_job_id") or (existing.preflight_job_id if existing else "") or ""),
        execution_job_id=str(getattr(job, "id", "") or ""),
        status=status,
        last_user_intent=existing.last_user_intent if existing else str(params.get("user_request") or ""),
        last_system_result=last_result,
        next_check=next_check,
        failure_reason=failure,
        approved_at=approved_at or (existing.approved_at if existing else None),
        last_evidence=existing.last_evidence if existing else None,
        last_logs=existing.last_logs if existing else None,
        last_verified_at=existing.last_verified_at if existing else None,
        updated_at=datetime.now(UTC).isoformat(),
        expires_at=_expires_at(),
    )
    save_thread_state(state)
    from aethos_core.continuity_intelligence.operational_focus_model import record_from_thread

    record_from_thread(state)
    return state


def sync_thread_on_approval(*, preflight_job: Any, execution_job: Any) -> OperationalThreadState:
    params = getattr(preflight_job, "params", None) or {}
    target = dict(params.get("target") or {})
    session_id = str(getattr(preflight_job, "session_id", None) or "default")
    state = OperationalThreadState(
        session_id=session_id,
        active_thread=f"{params.get('provider', 'railway')}_mutation",
        provider=str(params.get("provider") or "railway"),
        project=target.get("project_name"),
        environment=target.get("environment") or "production",
        service=str(params.get("target_name") or target.get("service_name") or ""),
        operation=str(params.get("operation_type") or ""),
        preflight_job_id=str(getattr(preflight_job, "id", "") or ""),
        execution_job_id=str(getattr(execution_job, "id", "") or ""),
        status="execution_queued",
        last_user_intent=str(params.get("user_request") or ""),
        last_system_result="Approval recorded — governed execution queued.",
        next_check="Wait for provider execution and verification evidence.",
        updated_at=datetime.now(UTC).isoformat(),
        expires_at=_expires_at(),
    )
    save_thread_state(state)
    from aethos_core.continuity_intelligence.operational_focus_model import record_from_thread

    record_from_thread(state)
    return state


def find_execution_job_for_service(*, session_id: str, service_phrase: str):
    from aethos_core.runtime.jobs import job_store

    norm = (service_phrase or "").strip().lower()
    for row in reversed(job_store.list_all()):
        if row.job_type != "mutation_execution":
            continue
        if str(getattr(row, "session_id", "") or "") != session_id:
            continue
        target = str(row.params.get("target_name") or "")
        project = str((row.params.get("target") or {}).get("project_name") or "")
        if norm in target.lower() or norm in project.lower() or target.lower() in norm:
            return row
    return None


def _summarize_result(
    params: dict[str, Any],
    artifact: dict[str, Any],
    failure: dict[str, Any] | None,
    restart_state: str,
    exec_state: str,
) -> str:
    if failure:
        return str(failure.get("failure_reason") or "Execution failed.")
    if restart_state in {"restart_unverified", "service_online_but_restart_unproven"}:
        return "Approval recorded, restart evidence missing."
    if params.get("restart_command_submitted") is True and restart_state:
        return f"Restart command submitted — verification state: {restart_state}."
    if exec_state == "provider_mutation_requested":
        return "Provider mutation requested — verification in progress."
    if params.get("verified"):
        return "Execution verified successfully."
    return str(params.get("lifecycle_summary") or artifact.get("execution_state") or "Execution updated.")


def _next_check(status: str, failure: dict[str, Any] | None) -> str:
    if failure:
        return str(failure.get("next_recommended_action") or "Review execution job and provider diagnostics.")
    if status in {"restart_unverified", "service_online_but_restart_unproven"}:
        return "Collect Railway restart evidence, recent logs, and service health."
    if status in {"stabilizing", "verification_pending", "verification_running", "execution_queued"}:
        return "Monitor execution job verification and provider evidence."
    return "Review latest execution evidence in Mission Control."
