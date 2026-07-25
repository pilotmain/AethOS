# SPDX-License-Identifier: Apache-2.0
"""Resolve short approval replies to pending Mission Control jobs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aethos_core.jobs.job_approval_guidance import extract_job_id
from aethos_core.jobs.session_approval_target import (
    SessionApprovalTarget,
    approval_route_for_job,
    get_session_approval_target,
    list_active_session_approval_targets,
    list_expired_unapproved_targets,
)
from aethos_core.jobs.short_approval_intent import is_short_approval_intent
from aethos_core.provider_e2e_execution.job_taxonomy import PROVIDER_E2E_ORCHESTRATION_JOB_TYPE
from aethos_core.provider_e2e_orchestration.approval_gate import ProviderE2EApprovalError, validate_approval_gate
from aethos_core.providers.railway.greenfield_deployment.greenfield_approval_gate import GreenfieldApprovalError
from aethos_core.providers.railway.greenfield_deployment.greenfield_preflight import (
    RAILWAY_GREENFIELD_PREFLIGHT_JOB_TYPE,
)
from aethos_core.providers.vercel.greenfield_deployment.greenfield_preflight import (
    VERCEL_GREENFIELD_PREFLIGHT_JOB_TYPE,
)


CHAT_SHORT_APPROVAL_JOB_TYPES = frozenset(
    {
        RAILWAY_GREENFIELD_PREFLIGHT_JOB_TYPE,
        VERCEL_GREENFIELD_PREFLIGHT_JOB_TYPE,
        PROVIDER_E2E_ORCHESTRATION_JOB_TYPE,
    }
)


@dataclass
class PendingOperationalApproval:
    job_id: str
    job_type: str
    provider: str
    action_type: str
    preflight_id: str
    approval_route: str
    label: str
    remembered: dict[str, Any]


def _pending_from_target(target: SessionApprovalTarget) -> PendingOperationalApproval:
    return PendingOperationalApproval(
        job_id=target.latest_pending_job_id,
        job_type=target.job_type,
        provider=target.provider,
        action_type=target.action_type,
        preflight_id=target.preflight_id,
        approval_route=target.approval_route,
        label=_label_for_target(target),
        remembered=target.to_dict(),
    )


def _label_for_target(target: SessionApprovalTarget) -> str:
    if target.job_type == RAILWAY_GREENFIELD_PREFLIGHT_JOB_TYPE:
        suffix = f" ({target.preflight_id})" if target.preflight_id else ""
        return f"Railway greenfield deployment{suffix}"
    if target.job_type == VERCEL_GREENFIELD_PREFLIGHT_JOB_TYPE:
        suffix = f" ({target.preflight_id})" if target.preflight_id else ""
        return f"Vercel greenfield deployment{suffix}"
    if target.job_type == PROVIDER_E2E_ORCHESTRATION_JOB_TYPE:
        return f"{target.provider or 'provider'} E2E orchestration"
    return target.job_type.replace("_", " ")


def _is_job_pending_approval(job: Any) -> bool:
    params = dict(getattr(job, "params", None) or {})
    job_type = str(getattr(job, "job_type", "") or "")
    if job_type in {RAILWAY_GREENFIELD_PREFLIGHT_JOB_TYPE, VERCEL_GREENFIELD_PREFLIGHT_JOB_TYPE}:
        return bool(params.get("approval_required")) and not params.get("greenfield_preflight_approved")
    if job_type == PROVIDER_E2E_ORCHESTRATION_JOB_TYPE:
        return not params.get("provider_e2e_approved") and str(params.get("execution_status") or "") in {
            "awaiting_approval",
            "",
        }
    return False


def list_pending_operational_approvals(*, session_id: str | None = None) -> list[PendingOperationalApproval]:
    from aethos_core.runtime.jobs import job_store
    from aethos_core.tenancy import DEFAULT_TENANT, get_current_tenant

    tenant = get_current_tenant()
    sid = (session_id or "").strip()
    tenant_wide = not sid or sid in {"default", "operator"}

    by_id: dict[str, PendingOperationalApproval] = {}

    if not tenant_wide:
        for target in list_active_session_approval_targets(session_id=sid):
            job = job_store.get(target.latest_pending_job_id)
            if not job:
                continue
            if str(getattr(job, "session_id", "") or "") != sid:
                continue
            if not _is_job_pending_approval(job):
                continue
            by_id[target.latest_pending_job_id] = _pending_from_target(target)

    for job in job_store.list_all():
        job_sid = str(getattr(job, "session_id", "") or "")
        if not tenant_wide and job_sid != sid:
            continue
        job_tenant = str((job.params or {}).get("tenant_id") or DEFAULT_TENANT)
        if job_tenant != tenant:
            continue
        if not _is_job_pending_approval(job):
            continue
        if job.id in by_id:
            continue
        lookup_sid = sid if not tenant_wide else job_sid
        remembered = get_session_approval_target(lookup_sid, job.id) if lookup_sid else None
        if remembered and remembered.mutation_performed:
            continue
        if lookup_sid and remembered and remembered in list_expired_unapproved_targets(session_id=lookup_sid):
            continue
        approval_route = approval_route_for_job(job_id=job.id, job_type=str(job.job_type))
        by_id[job.id] = PendingOperationalApproval(
            job_id=job.id,
            job_type=str(job.job_type),
            provider=str((job.params or {}).get("provider") or ""),
            action_type=str((job.params or {}).get("action_type") or "provider_e2e_orchestration"),
            preflight_id=str((job.params or {}).get("preflight_id") or ""),
            approval_route=approval_route,
            label=_label_for_target(
                SessionApprovalTarget(
                    session_id=job_sid,
                    latest_pending_job_id=job.id,
                    job_type=str(job.job_type),
                    provider=str((job.params or {}).get("provider") or ""),
                    action_type=str((job.params or {}).get("action_type") or ""),
                    preflight_id=str((job.params or {}).get("preflight_id") or ""),
                    approval_route=approval_route,
                )
            ),
            remembered=remembered.to_dict() if remembered else {},
        )
    return list(by_id.values())


def compose_no_active_pending_reply() -> str:
    return (
        "No active pending approval found in this session.\n\n"
        "Run a governed preflight first, or reply with an explicit job id such as `approve job-abc123`."
    )


def compose_disambiguation_reply(pending: list[PendingOperationalApproval]) -> str:
    lines = [
        "Multiple pending approvals exist in this session. Reply with the job id to approve:",
        "",
    ]
    for row in pending:
        lines.append(f"- `{row.job_id}` — {row.label}")
    return "\n".join(lines)


def compose_blocker_reply(*, code: str, meaning: str, required_action: str, safe_next_command: str) -> str:
    lines = [
        "Approval could not be applied.",
        "",
        "Blocker:",
        f"- **Code:** `{code}`",
        f"- **Meaning:** {meaning}",
        f"- **Required action:** {required_action}",
    ]
    if safe_next_command:
        lines.append(f"- **Safe next command:** `{safe_next_command}`")
    return "\n".join(lines)


def compose_greenfield_success_reply(*, job_id: str, preflight_id: str) -> str:
    return "\n".join(
        [
            "Approval accepted for Railway greenfield deployment.",
            "",
            f"Job: `{job_id}`",
            f"Preflight: `{preflight_id}`",
            "",
            "Execution has started under Mission Control.",
            "",
            "I will apply env vars from secure references, create/redeploy the Railway service, "
            "poll deployment status, verify health, and report the final result.",
            "",
            "No secret values will be shown.",
        ]
    )


def compose_provider_e2e_success_reply(*, job_id: str, provider: str) -> str:
    return "\n".join(
        [
            f"Approval accepted for {provider or 'provider'} E2E orchestration.",
            "",
            f"Job: `{job_id}`",
            "",
            "Execution has started under Mission Control.",
            "",
            "No secret values will be shown.",
        ]
    )


def compose_supabase_env_completion_success_reply(*, job_id: str) -> str:
    return "\n".join(
        [
            "Approval accepted for Supabase env completion.",
            "",
            f"Job: `{job_id}`",
            "",
            "Running governed chain: secure store → Vercel env → redeploy → verify.",
            "If browser automation is on, log in to Supabase when the window opens.",
            "",
            "No secret values will be shown in chat.",
        ]
    )


def _audit_chat_approval_resolution(*, pending: PendingOperationalApproval, session_id: str, route_id: str) -> None:
    from aethos_core.connections.credential_audit import append_credential_audit_event

    append_credential_audit_event(
        event="chat_approval_resolved",
        provider=str(pending.provider or "operational"),
        credential_id=pending.job_id,
        validation_status=route_id,
        detail=f"session={session_id} job_type={pending.job_type}",
    )


def _chat_approval_target_valid(pending: PendingOperationalApproval, *, session_id: str) -> tuple[bool, str]:
    if pending.job_type not in CHAT_SHORT_APPROVAL_JOB_TYPES:
        from aethos_core.provider_e2e_orchestration.env_completion.supabase_constants import (
            SUPABASE_ENV_COMPLETION_JOB_TYPE,
        )

        if pending.job_type != SUPABASE_ENV_COMPLETION_JOB_TYPE:
            return False, "unsupported_job_type"
    remembered = pending.remembered or {}
    remembered_session = str(remembered.get("session_id") or "").strip()
    if remembered_session and remembered_session != session_id:
        return False, "session_mismatch"
    if remembered:
        expires_at = remembered.get("expires_at")
        if expires_at is not None:
            try:
                if float(expires_at) < __import__("time").time():
                    return False, "expired"
            except (TypeError, ValueError):
                pass
    return True, ""


def _execute_approval(pending: PendingOperationalApproval, *, session_id: str) -> tuple[str, dict[str, str]]:
    ok, blocker = _chat_approval_target_valid(pending, session_id=session_id)
    if not ok:
        body = compose_blocker_reply(
            code=blocker,
            meaning="Chat approval target did not match session, expiry, or allowlist.",
            required_action="Re-run preflight or approve via Mission Control.",
            safe_next_command="",
        )
        return body, {"route_id": "pending_job_approval_blocked", "blocker": blocker, "job_id": pending.job_id}
    from aethos_core.jobs.session_approval_target import mark_session_approval_mutation_performed
    from aethos_core.provider_e2e_orchestration.approval_flow import approve_provider_e2e_orchestration
    from aethos_core.providers.railway.greenfield_deployment.greenfield_approval_flow import (
        approve_railway_greenfield_preflight,
    )
    from aethos_core.providers.vercel.greenfield_deployment.greenfield_preflight import (
        VERCEL_GREENFIELD_PREFLIGHT_JOB_TYPE,
        approve_vercel_greenfield_preflight,
    )
    from aethos_core.runtime.jobs import job_store

    job = job_store.get(pending.job_id)
    if not job:
        body = compose_blocker_reply(
            code="job_not_found",
            meaning="The remembered pending job no longer exists.",
            required_action="Re-run the governed preflight.",
            safe_next_command="",
        )
        return body, {"route_id": "pending_job_approval_blocked", "blocker": "job_not_found"}

    if pending.job_type == RAILWAY_GREENFIELD_PREFLIGHT_JOB_TYPE:
        try:
            approved, meta = approve_railway_greenfield_preflight(
                pending.job_id,
                session_id=session_id,
                remembered=pending.remembered,
            )
        except GreenfieldApprovalError as exc:
            gate = exc.result
            body = compose_blocker_reply(
                code=str(gate.failure_state or "approval_blocked"),
                meaning=gate.detail or "Greenfield approval blocked.",
                required_action=gate.required_action or "Resolve the blocker, then reply approve again.",
                safe_next_command=gate.safe_next_command or "approve",
            )
            return body, {
                "route_id": "pending_job_approval_blocked",
                "blocker": str(gate.failure_state or "approval_blocked"),
                "job_id": pending.job_id,
            }

        preflight_id = str(meta.get("preflight_id") or pending.preflight_id or "")
        body = compose_greenfield_success_reply(job_id=approved.id, preflight_id=preflight_id)
        _audit_chat_approval_resolution(pending=pending, session_id=session_id, route_id="pending_job_approval_resolved")
        return body, {
            "route_id": "pending_job_approval_resolved",
            "job_id": approved.id,
            "preflight_id": preflight_id,
            "orchestration_job_id": str(meta.get("orchestration_job_id") or ""),
            "approval_route": pending.approval_route,
            "mutation_performed": "true",
        }

    if pending.job_type == VERCEL_GREENFIELD_PREFLIGHT_JOB_TYPE:
        try:
            approved, meta = approve_vercel_greenfield_preflight(
                pending.job_id,
                session_id=session_id,
                remembered=pending.remembered,
            )
        except GreenfieldApprovalError as exc:
            gate = exc.result
            body = compose_blocker_reply(
                code=str(gate.failure_state or "approval_blocked"),
                meaning=gate.detail or "Greenfield approval blocked.",
                required_action=gate.required_action or "Resolve the blocker, then reply approve again.",
                safe_next_command=gate.safe_next_command or "approve",
            )
            return body, {
                "route_id": "pending_job_approval_blocked",
                "blocker": str(gate.failure_state or "approval_blocked"),
                "job_id": pending.job_id,
            }

        preflight_id = str(meta.get("preflight_id") or pending.preflight_id or "")
        body = compose_greenfield_success_reply(job_id=approved.id, preflight_id=preflight_id).replace(
            "Railway", "Vercel"
        )
        _audit_chat_approval_resolution(pending=pending, session_id=session_id, route_id="pending_job_approval_resolved")
        return body, {
            "route_id": "pending_job_approval_resolved",
            "job_id": approved.id,
            "preflight_id": preflight_id,
            "orchestration_job_id": str(meta.get("orchestration_job_id") or ""),
            "approval_route": pending.approval_route,
            "mutation_performed": "true",
        }

    if pending.job_type == PROVIDER_E2E_ORCHESTRATION_JOB_TYPE:
        gate = validate_approval_gate(job, for_execution=False)
        if not gate.ok:
            body = compose_blocker_reply(
                code=str(gate.failure_state or "approval_blocked"),
                meaning=gate.detail or "Provider E2E approval blocked.",
                required_action="Resolve the blocker, then reply approve again.",
                safe_next_command="approve",
            )
            return body, {
                "route_id": "pending_job_approval_blocked",
                "blocker": str(gate.failure_state or "approval_blocked"),
                "job_id": pending.job_id,
            }
        try:
            approved, _meta = approve_provider_e2e_orchestration(pending.job_id)
        except ProviderE2EApprovalError as exc:
            body = compose_blocker_reply(
                code="approval_blocked",
                meaning=str(exc),
                required_action="Resolve the blocker, then reply approve again.",
                safe_next_command="approve",
            )
            return body, {"route_id": "pending_job_approval_blocked", "blocker": "approval_blocked", "job_id": pending.job_id}

        mark_session_approval_mutation_performed(session_id=session_id, job_id=pending.job_id)
        body = compose_provider_e2e_success_reply(
            job_id=approved.id,
            provider=str((approved.params or {}).get("provider") or pending.provider),
        )
        _audit_chat_approval_resolution(pending=pending, session_id=session_id, route_id="pending_job_approval_resolved")
        return body, {
            "route_id": "pending_job_approval_resolved",
            "job_id": approved.id,
            "approval_route": pending.approval_route,
            "mutation_performed": "true",
        }

    from aethos_core.provider_e2e_orchestration.env_completion.supabase_constants import (
        SUPABASE_ENV_COMPLETION_JOB_TYPE,
    )
    from aethos_core.provider_e2e_orchestration.env_completion.supabase_approval import (
        SupabaseEnvCompletionApprovalError,
        approve_supabase_env_completion,
        validate_supabase_env_completion_gate,
    )

    if pending.job_type == SUPABASE_ENV_COMPLETION_JOB_TYPE:
        gate = validate_supabase_env_completion_gate(job, for_execution=False)
        if not gate.ok:
            body = compose_blocker_reply(
                code=str(gate.failure_state or "approval_blocked"),
                meaning=gate.detail or "Supabase env completion approval blocked.",
                required_action="Resolve the blocker, then reply approve again.",
                safe_next_command="approve",
            )
            return body, {
                "route_id": "pending_job_approval_blocked",
                "blocker": str(gate.failure_state or "approval_blocked"),
                "job_id": pending.job_id,
            }
        try:
            approved, _meta = approve_supabase_env_completion(pending.job_id)
        except SupabaseEnvCompletionApprovalError as exc:
            body = compose_blocker_reply(
                code="approval_blocked",
                meaning=str(exc),
                required_action="Resolve the blocker, then reply approve again.",
                safe_next_command="approve",
            )
            return body, {"route_id": "pending_job_approval_blocked", "blocker": "approval_blocked", "job_id": pending.job_id}

        mark_session_approval_mutation_performed(session_id=session_id, job_id=pending.job_id)
        body = compose_supabase_env_completion_success_reply(job_id=approved.id)
        _audit_chat_approval_resolution(pending=pending, session_id=session_id, route_id="pending_job_approval_resolved")
        return body, {
            "route_id": "pending_job_approval_resolved",
            "job_id": approved.id,
            "approval_route": pending.approval_route,
            "mutation_performed": "true",
        }

    body = compose_blocker_reply(
        code="unsupported_job_type",
        meaning=f"Job type `{pending.job_type}` is not supported for short approval resolution.",
        required_action="Use Mission Control to approve this job explicitly.",
        safe_next_command="",
    )
    return body, {"route_id": "pending_job_approval_blocked", "blocker": "unsupported_job_type", "job_id": pending.job_id}


def _defer_short_approval_to_other_lanes(text: str, session_id: str) -> bool:
    from aethos_core.providers.github.workflow_lane.workflow_lane_router import _is_approve_with_state

    return bool(_is_approve_with_state(text, session_id=session_id))


def resolve_short_approval(text: str, *, session_id: str = "default") -> tuple[str, str, dict[str, str]] | None:
    if not is_short_approval_intent(text):
        return None

    explicit_job_id = extract_job_id(text)
    pending_rows = list_pending_operational_approvals(session_id=session_id)
    if not pending_rows:
        expired_rows = list_expired_unapproved_targets(session_id=session_id)
        if len(expired_rows) == 1:
            expired = expired_rows[0]
            from aethos_core.runtime.jobs import job_store

            job = job_store.get(expired.latest_pending_job_id)
            if job and _is_job_pending_approval(job):
                body = compose_blocker_reply(
                    code="expired",
                    meaning="Approval target expired for this session.",
                    required_action="Re-run the Railway greenfield preflight to obtain a fresh approval target.",
                    safe_next_command="Repeat the local workspace Railway deployment request.",
                )
                return body, "pending_job_approval_blocked", {
                    "route_id": "pending_job_approval_blocked",
                    "blocker": "expired",
                    "job_id": expired.latest_pending_job_id,
                }
        if _defer_short_approval_to_other_lanes(text, session_id):
            return None
        return compose_no_active_pending_reply(), "pending_job_approval_none", {
            "route_id": "pending_job_approval_none",
            "session_id": session_id,
        }

    if explicit_job_id:
        selected = next((row for row in pending_rows if row.job_id == explicit_job_id), None)
        if not selected:
            body = compose_blocker_reply(
                code="job_not_pending",
                meaning=f"`{explicit_job_id}` is not an active pending approval in this session.",
                required_action="Choose one of the pending jobs listed below or re-run preflight.",
                safe_next_command="approve",
            )
            if len(pending_rows) > 1:
                body = body + "\n\n" + compose_disambiguation_reply(pending_rows)
            return body, "pending_job_approval_blocked", {
                "route_id": "pending_job_approval_blocked",
                "blocker": "job_not_pending",
                "job_id": explicit_job_id,
            }
        body, meta = _execute_approval(selected, session_id=session_id)
        return body, str(meta.get("route_id") or "pending_job_approval_resolved"), meta

    if len(pending_rows) > 1:
        body = compose_disambiguation_reply(pending_rows)
        return body, "pending_job_approval_disambiguation", {
            "route_id": "pending_job_approval_disambiguation",
            "pending_count": str(len(pending_rows)),
        }

    body, meta = _execute_approval(pending_rows[0], session_id=session_id)
    return body, str(meta.get("route_id") or "pending_job_approval_resolved"), meta


def route_short_approval_turn(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    return resolve_short_approval(text, session_id=session_id)
