# SPDX-License-Identifier: Apache-2.0
"""Job approval routing and guidance — mutation preflight + durable jobs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from aethos_core.config import get_settings
from aethos_core.jobs.job_state import get_job as get_durable_job
from aethos_core.mission_control.visible_navigation_registry import (
    INTERNAL_SURFACE_DURABLE_JOBS,
    INTERNAL_SURFACE_MUTATION_APPROVAL,
    contains_hidden_navigation_leakage,
    resolve_visible_navigation_path,
    sanitize_operator_navigation_copy,
)
from aethos_core.operations.mutations.mutation_execution_flow import MUTATION_APPROVABLE_STATUSES
from aethos_core.runtime.job_types import uses_mutation_preflight

APPROVAL_ACTION_MUTATION = "Approve Governed Mutation"
APPROVAL_ACTION_READONLY = "Approve Read-Only Execution"
APPROVAL_ACTION_DURABLE = "Approve Governed Job"


def mutation_approval_surface(*, mode: str = "operator") -> str:
    return resolve_visible_navigation_path(internal_surface=INTERNAL_SURFACE_MUTATION_APPROVAL, mode=mode)


def durable_approval_surface(*, mode: str = "operator") -> str:
    return resolve_visible_navigation_path(internal_surface=INTERNAL_SURFACE_DURABLE_JOBS, mode=mode)


REVIEW_ITEMS_MUTATION = ["blast_radius", "rollback_plan", "risk_tier", "provider_target"]
REVIEW_ITEMS_READONLY = ["preflight_summary", "risk_tier", "provider_target"]
REVIEW_ITEMS_DURABLE = ["job_type", "entity_name", "params"]

_JOB_ID_RX = re.compile(r"\b((?:job|dj)-[a-f0-9]+)\b", re.I)
_APPROVAL_INTENT_RX = re.compile(
    r"\b("
    r"where\s+(?:do\s+i|can\s+i|to)\s+approve"
    r"|how\s+(?:do\s+i|to)\s+approve"
    r"|where\s+is\s+the\s+approval"
    r"|where\s+can\s+i\s+approve"
    r"|approve\s+(?:this|the|my)\s+(?:job|restart|mutation)"
    r"|approve\s+(?:job|dj)-"
    r")\b",
    re.I,
)


@dataclass
class JobApprovalGuidance:
    ok: bool
    found: bool
    job_id: str
    job_store: str  # tracked | durable
    job_type: str | None = None
    approval_required: bool = False
    approval_state: str = "not_applicable"
    approval_surface: str | None = None
    approval_action_label: str | None = None
    review_items: list[str] | None = None
    post_approval_behavior: str | None = None
    ui_action_available: bool = False
    execution_started: bool = False
    current_status: str | None = None
    latest_summary: str | None = None
    next_step: str | None = None
    reason: str | None = None
    provider: str | None = None
    operation_type: str | None = None
    risk_tier: str | None = None
    blast_radius: dict[str, Any] | None = None
    rollback_plan: dict[str, Any] | None = None
    target_name: str | None = None
    wiring_gap: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


def build_mutation_approval_metadata(*, preflight_status: str, mode: str = "operator") -> dict[str, Any]:
    pending = preflight_status in MUTATION_APPROVABLE_STATUSES
    visible = mutation_approval_surface(mode=mode)
    return {
        "approval_required": pending,
        "approval_surface": visible,
        "approval_surface_internal": INTERNAL_SURFACE_MUTATION_APPROVAL,
        "approval_action_label": APPROVAL_ACTION_MUTATION,
        "approval_state": "pending_approval" if pending else "not_required",
        "review_items": list(REVIEW_ITEMS_MUTATION),
        "post_approval_behavior": "execute_governed_mutation",
        "ui_action_available": pending,
    }


def build_no_action_preflight_metadata(*, reason: str, mode: str = "operator") -> dict[str, Any]:
    return {
        "approval_required": False,
        "approval_surface": mutation_approval_surface(mode=mode),
        "approval_surface_internal": INTERNAL_SURFACE_MUTATION_APPROVAL,
        "approval_action_label": APPROVAL_ACTION_MUTATION,
        "approval_state": "not_required",
        "review_items": [],
        "post_approval_behavior": "none",
        "ui_action_available": False,
        "preflight_status": "no_action_available",
        "no_action_reason": reason,
    }


def build_readonly_approval_metadata(*, preflight_status: str, mode: str = "operator") -> dict[str, Any]:
    pending = preflight_status in {"ready_for_approval", "ready_for_readonly_diagnostic"}
    visible = mutation_approval_surface(mode=mode)
    return {
        "approval_required": pending,
        "approval_surface": visible,
        "approval_surface_internal": INTERNAL_SURFACE_MUTATION_APPROVAL,
        "approval_action_label": APPROVAL_ACTION_READONLY,
        "approval_state": "pending_approval" if pending else "not_required",
        "review_items": list(REVIEW_ITEMS_READONLY),
        "post_approval_behavior": "execute_readonly_diagnostic",
        "ui_action_available": True,
    }


def extract_job_id(text: str) -> str | None:
    match = _JOB_ID_RX.search(text)
    return match.group(1) if match else None


def is_job_approval_intent(text: str) -> bool:
    if not _JOB_ID_RX.search(text):
        return False
    lower = text.lower()
    if _APPROVAL_INTENT_RX.search(lower):
        return True
    if re.search(r"\bapprove\b", lower) and _JOB_ID_RX.search(text):
        return True
    if re.search(r"\bwhere\b.*\bapprove\b", lower):
        return True
    return False


def _tracked_guidance(job_id: str) -> JobApprovalGuidance | None:
    from aethos_core.operations.preflight_execution import APPROVABLE_STATUSES as READONLY_APPROVABLE_STATUSES
    from aethos_core.runtime.jobs import job_store

    job = job_store.get(job_id)
    if not job:
        return None

    params = dict(job.params or {})
    pf = dict(params.get("mutation_preflight") or {})
    preflight_status = str(params.get("preflight_status") or pf.get("preflight_status") or "")
    provider = str(pf.get("provider") or params.get("provider") or "")
    operation_type = str(pf.get("operation_type") or params.get("operation_type") or "")
    target_name = pf.get("target_name") or params.get("target_name")
    target_resolved = bool(params.get("target_resolved") or pf.get("target_resolved"))
    target_payload = params.get("target") or pf.get("target")
    if isinstance(target_payload, dict) and target_payload.get("resolved"):
        target_resolved = True
    risk_tier = str(params.get("risk_tier") or pf.get("risk_tier") or "")
    blast_radius = params.get("blast_radius") or pf.get("blast_radius")
    rollback_plan = params.get("rollback_plan") or pf.get("rollback_plan")
    exec_job_id = params.get("mutation_execution_job_id") or pf.get("mutation_execution_job_id")
    already_approved = bool(params.get("mutation_execution_approved") or pf.get("mutation_execution_approved"))

    if uses_mutation_preflight(job.job_type):
        meta = build_mutation_approval_metadata(preflight_status=preflight_status)
        ui_available = bool(meta["ui_action_available"]) and get_settings().mutation_execution_enabled
        pending = (
            meta["approval_required"]
            and job.status.value == "completed"
            and params.get("is_current") is not False
            and not already_approved
        )
        execution_started = bool(exec_job_id) or already_approved
        wiring_gap = None
        reason = str(params.get("no_action_reason") or pf.get("no_action_reason") or "") or None
        target_unresolved = preflight_status == "needs_information" or (
            not target_resolved and not target_name
        )
        if preflight_status == "no_action_available":
            pending = False
            ui_available = False
            reason = reason or "no failed workflow run found"
        if pending and not get_settings().mutation_execution_enabled:
            wiring_gap = "Mutation execution is disabled — set MUTATION_EXECUTION_ENABLED=true before approval."
        elif pending and preflight_status not in MUTATION_APPROVABLE_STATUSES:
            if preflight_status == "no_action_available":
                wiring_gap = str(
                    params.get("no_action_reason")
                    or pf.get("no_action_reason")
                    or "No failed workflow run found — approval is not available."
                )
            elif preflight_status in ("needs_credential", "needs_credential_repair"):
                from aethos_core.credentials.credential_guidance import compose_missing_credential_reply

                pf = dict(params.get("mutation_preflight") or {})
                preflight = {**pf, **params}
                preflight.setdefault("preflight_status", preflight_status)
                wiring_gap = (
                    compose_missing_credential_reply(preflight)
                    or "Provider mutation credentials are missing — configure credentials before approval."
                )
            else:
                wiring_gap = "Preflight is not ready for governed mutation approval yet."
        elif target_unresolved:
            wiring_gap = "Railway target is unresolved — resolve the target before approval."
            pending = False
            ui_available = False

        return JobApprovalGuidance(
            ok=True,
            found=True,
            job_id=job_id,
            job_store="tracked",
            job_type=job.job_type,
            approval_required=bool(meta["approval_required"]),
            approval_state="approved" if execution_started else ("pending_approval" if pending else str(meta["approval_state"])),
            approval_surface=str(meta["approval_surface"]),
            approval_action_label=str(meta["approval_action_label"]),
            review_items=list(meta["review_items"]),
            post_approval_behavior=str(meta["post_approval_behavior"]),
            ui_action_available=ui_available and pending,
            execution_started=execution_started,
            current_status=job.status.value,
            latest_summary=(job.result_summary or job.result or "")[:400] or None,
            next_step=_mutation_next_step(
                pending=pending,
                execution_started=execution_started,
                exec_job_id=exec_job_id,
                operation_type=operation_type,
                provider=provider,
            ),
            provider=provider or None,
            operation_type=operation_type or None,
            risk_tier=risk_tier or None,
            blast_radius=blast_radius if isinstance(blast_radius, dict) else None,
            rollback_plan=rollback_plan if isinstance(rollback_plan, dict) else None,
            target_name=str(target_name) if target_name else None,
            wiring_gap=wiring_gap,
            reason=reason,
        )

    if str(job.job_type).endswith("_preflight") or params.get("operation_preflight"):
        meta = build_readonly_approval_metadata(preflight_status=preflight_status)
        pending = meta["approval_required"] and job.status.value == "completed"
        exec_job_id = params.get("readonly_execution_job_id") or params.get("execution_job_id")
        execution_started = bool(exec_job_id)
        return JobApprovalGuidance(
            ok=True,
            found=True,
            job_id=job_id,
            job_store="tracked",
            job_type=job.job_type,
            approval_required=bool(meta["approval_required"]),
            approval_state="pending_approval" if pending and not execution_started else "approved" if execution_started else "not_required",
            approval_surface=str(meta["approval_surface"]),
            approval_action_label=str(meta["approval_action_label"]),
            review_items=list(meta["review_items"]),
            post_approval_behavior=str(meta["post_approval_behavior"]),
            ui_action_available=pending and preflight_status in READONLY_APPROVABLE_STATUSES,
            execution_started=execution_started,
            current_status=job.status.value,
            latest_summary=(job.result_summary or job.result or "")[:400] or None,
            next_step=(
                f"Approve read-only execution in **{mutation_approval_surface()}**."
                if pending
                else None
            ),
            provider=provider or None,
            operation_type=operation_type or None,
            risk_tier=risk_tier or None,
            target_name=str(target_name) if target_name else None,
        )

    return JobApprovalGuidance(
        ok=True,
        found=True,
        job_id=job_id,
        job_store="tracked",
        job_type=job.job_type,
        approval_required=False,
        approval_state="not_required",
        current_status=job.status.value,
        latest_summary=(job.result_summary or job.result or "")[:400] or None,
        next_step="This tracked job does not require governed mutation approval.",
    )


def _mutation_next_step(
    *,
    pending: bool,
    execution_started: bool,
    exec_job_id: Any,
    operation_type: str = "",
    provider: str = "",
) -> str | None:
    if execution_started:
        if exec_job_id:
            return f"Governed mutation execution job `{exec_job_id}` is in progress or complete."
        return "Mutation approval recorded — execution has started or completed."
    if pending:
        surface = mutation_approval_surface()
        op = str(operation_type or "mutation").replace("_", " ")
        prov = provider or "provider"
        return (
            f"Open the pending **{prov} {op}** job in **{surface}**, "
            f"review blast radius, rollback plan, risk tier, and provider target, "
            f"then click **{APPROVAL_ACTION_MUTATION}**."
        )
    return None


def _finalize_operator_reply(reply: str) -> str:
    cleaned = sanitize_operator_navigation_copy(reply, mode="operator")
    assert not contains_hidden_navigation_leakage(cleaned, mode="operator"), "hidden navigation leaked into operator reply"
    return cleaned


def _durable_guidance(job_id: str, session_id: str | None = None) -> JobApprovalGuidance | None:
    job = get_durable_job(job_id)
    if not job:
        return None
    if session_id and str(job.get("session_id") or "") != session_id:
        return None

    status = str(job.get("status") or "")
    params = dict(job.get("params") or {})
    pending = status == "awaiting_approval" or bool(params.get("approval_required"))
    visible = durable_approval_surface()
    return JobApprovalGuidance(
        ok=True,
        found=True,
        job_id=job_id,
        job_store="durable",
        job_type=str(job.get("job_type") or ""),
        approval_required=pending,
        approval_state="pending_approval" if pending else status,
        approval_surface=visible,
        approval_action_label=APPROVAL_ACTION_DURABLE,
        review_items=list(REVIEW_ITEMS_DURABLE),
        post_approval_behavior="dispatch_durable_job",
        ui_action_available=False,
        execution_started=status in {"running", "completed", "dispatching", "awaiting_callback"},
        current_status=status,
        latest_summary=str(job.get("error") or job.get("artifact_ref") or "")[:400] or None,
        next_step=(
            f"Open **{visible}** → `{job_id}`. "
            "The durable job approval action is not wired in the UI yet — dispatch after approval is pending."
            if pending
            else None
        ),
        wiring_gap="Durable job UI approval action is not wired yet." if pending else None,
        target_name=str(job.get("entity_name") or "") or None,
    )


def get_job_approval_guidance(job_id: str, session_id: str | None = None) -> JobApprovalGuidance:
    normalized = job_id.strip()
    if normalized.startswith("dj-"):
        durable = _durable_guidance(normalized, session_id=session_id)
        if durable:
            return durable
    tracked = _tracked_guidance(normalized)
    if tracked:
        return tracked
    if not normalized.startswith("dj-"):
        durable = _durable_guidance(normalized, session_id=session_id)
        if durable:
            return durable
    return JobApprovalGuidance(
        ok=True,
        found=False,
        job_id=normalized,
        job_store="unknown",
        approval_required=False,
        approval_state="not_found",
        reason="job_not_found",
        next_step=(
            f"Check **{mutation_approval_surface()}** or **{durable_approval_surface()}** for recent jobs."
        ),
    )


def compose_job_approval_guidance_reply(text: str, *, session_id: str = "default") -> str | None:
    job_id = extract_job_id(text)
    if not job_id:
        return None
    if not is_job_approval_intent(text) and not re.search(r"\bapprove\b", text, re.I):
        return None

    guidance = get_job_approval_guidance(job_id, session_id=session_id)
    surface = mutation_approval_surface()
    durable_surface = durable_approval_surface()

    if not guidance.found:
        return _finalize_operator_reply(
            f"I couldn't find `{job_id}` in the current AethOS job store.\n\n"
            f"Check **{surface}** for recent governed mutation preflights, "
            f"or **{durable_surface}** for background agent jobs."
        )

    if guidance.execution_started and guidance.approval_state != "pending_approval":
        lines = [
            f"`{job_id}` has already passed approval — execution has started or completed.",
            f"**Current state:** {guidance.current_status or 'unknown'}.",
        ]
        if guidance.latest_summary:
            lines.append(f"**Latest update:** {guidance.latest_summary}")
        if guidance.next_step:
            lines.append(guidance.next_step)
        return _finalize_operator_reply("\n\n".join(lines))

    if not guidance.approval_required:
        return _finalize_operator_reply(
            f"`{job_id}` ({guidance.job_type or 'job'}) does not require governed mutation approval.\n\n"
            f"**Current state:** {guidance.current_status or 'unknown'}."
            + (f"\n\n{guidance.latest_summary}" if guidance.latest_summary else "")
        )

    if guidance.wiring_gap and not guidance.ui_action_available:
        return _finalize_operator_reply(
            f"The mutation preflight completed successfully, but the approval action is not currently exposed in the visible operator workflow.\n\n"
            f"**Expected location:** {guidance.approval_surface or surface} → `{job_id}`\n\n"
            f"**Needed:** {guidance.wiring_gap}\n\n"
            f"**Current status:** approval pending — no restart has been performed yet."
        )

    op = str(guidance.operation_type or "mutation").replace("_", " ")
    prov = guidance.provider or "provider"
    target_hint = f" ({guidance.target_name})" if guidance.target_name else ""

    return _finalize_operator_reply(
        f"Approve it in **{guidance.approval_surface or surface}**.\n\n"
        f"Open the pending **{prov} {op}** job{target_hint}, review the **blast radius** and **rollback plan**, "
        f"then click **{guidance.approval_action_label or APPROVAL_ACTION_MUTATION}**.\n\n"
        f"**No {op} has been performed yet.**"
    )


def list_pending_mutation_approvals(*, session_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    from aethos_core.runtime.jobs import job_store
    from aethos_core.tenancy import DEFAULT_TENANT, get_current_tenant

    lookup_sessions: set[str] | None = None
    if session_id:
        from aethos_core.channels.session_alias import session_ids_for_lookup

        lookup_sessions = set(session_ids_for_lookup(session_id))
    tenant = get_current_tenant()

    rows: list[dict[str, Any]] = []
    for job in job_store.list_all():
        if lookup_sessions is not None:
            job_sid = str(getattr(job, "session_id", "") or "")
            if job_sid not in lookup_sessions:
                continue
        job_tenant = str((job.params or {}).get("tenant_id") or DEFAULT_TENANT)
        if job_tenant != tenant:
            continue
        if not uses_mutation_preflight(job.job_type):
            continue
        guidance = _tracked_guidance(job.id)
        if not guidance or not guidance.approval_required:
            continue
        if guidance.approval_state != "pending_approval":
            continue
        rows.append(guidance.to_dict())
        if len(rows) >= limit:
            break
    return rows
