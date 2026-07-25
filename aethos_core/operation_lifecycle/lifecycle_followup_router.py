# SPDX-License-Identifier: Apache-2.0
"""Lifecycle follow-up routing — approval, credential, and completion continuity."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.credentials.credential_guidance import compose_missing_credential_reply
from aethos_core.operation_lifecycle.lifecycle_resolver import (
    compose_duplicate_mutation_reply,
    get_latest_operation_state,
    has_recent_mutation_execution,
    is_blocked_by_credentials,
    is_duplicate_mutation_request,
    is_operation_verified,
    is_waiting_for_approval,
)
from aethos_core.operation_lifecycle.operation_state_store import OperationLifecycleState

_APPROVAL_FOLLOWUP_RX = re.compile(
    r"\b("
    r"why\s+(?:can'?t|cannot)\s+i\s+approve"
    r"|why\s+is\s+(?:it|this)\s+not\s+approvable"
    r")\b",
    re.I,
)

_CREDENTIAL_FOLLOWUP_RX = re.compile(
    r"\b("
    r"what\s+credential\s+(?:is\s+)?missing"
    r"|how\s+(?:do\s+i|to)\s+(?:fix|set\s*up|configure)\s+credentials?"
    r"|what\s+do\s+i\s+need\s+(?:to\s+)?restart"
    r")\b",
    re.I,
)

_COMPLETION_FOLLOWUP_RX = re.compile(
    r"\b("
    r"did\s+(?:it|the\s+\w+)\s+already\s+restart"
    r"|did\s+the\s+restart\s+(?:finish|complete|work)"
    r"|did\s+the\s+restart\s+(?:actually\s+)?(?:happen|work)"
    r"|what\s+happened\s+after\s+approval"
    r"|is\s+it\s+done"
    r"|can\s+i\s+retry"
    r"|update\s+please"
    r"|any\s+update"
    r"|status\s+update"
    r")\b",
    re.I,
)

_JOB_ID_RX = re.compile(r"\b((?:job|dj)-[a-f0-9]+)\b", re.I)


def is_lifecycle_followup_intent(text: str) -> bool:
    raw = text or ""
    if _APPROVAL_FOLLOWUP_RX.search(raw):
        return True
    if _CREDENTIAL_FOLLOWUP_RX.search(raw):
        return True
    if _COMPLETION_FOLLOWUP_RX.search(raw):
        return True
    return False


def _resolve_state(text: str, *, session_id: str) -> OperationLifecycleState | None:
    job_match = _JOB_ID_RX.search(text)
    if job_match:
        from aethos_core.runtime.jobs import job_store

        job = job_store.get(job_match.group(1))
        if job:
            from aethos_core.operation_lifecycle.operation_state_store import build_operation_state_from_job

            return build_operation_state_from_job(job)
    return get_latest_operation_state(session_id=session_id, text=text)


def _compose_completed_credential_reply(state: OperationLifecycleState) -> str:
    target = state.target_path()
    lines = [
        "No credential is currently blocking this operation.",
        "",
        f"**Latest {state.operation.replace('_', ' ')} execution:**",
        f"- status: {state.execution_status}",
        f"- target: {target}",
    ]
    if state.verification_status not in {"none", ""}:
        lines.append(f"- verification: {state.verification_status}")
    if state.latest_summary:
        lines.append(f"- summary: {state.latest_summary}")
    if state.execution_job_id:
        lines.append(f"- execution job: `{state.execution_job_id}`")
    lines.append("")
    lines.append("The restart already completed — there is nothing left to approve for that execution.")
    return "\n".join(lines)


def _compose_completed_approval_reply(state: OperationLifecycleState) -> str:
    target = state.target_path()
    op = state.operation.replace("_", " ")
    verified = is_operation_verified(state)
    if state.provider == "github" and state.operation == "workflow_rerun":
        from aethos_core.runtime.jobs import job_store

        if state.execution_job_id:
            job = job_store.get(state.execution_job_id)
            if job:
                proactive = str(job.params.get("proactive_verification_reply") or job.params.get("chain_summary") or "")
                if proactive:
                    return (
                        f"The **GitHub workflow rerun** for **{target}** already completed.\n\n{proactive}\n\n"
                        f"Execution job: `{state.execution_job_id}`."
                    )
    if verified:
        lead = f"You do not need to approve anything — the **{op}** for **{target}** already completed and verified."
    else:
        lead = (
            f"You do not need to approve anything — the **{op}** for **{target}** was already submitted. "
            "Railway deployment is **not confirmed yet**; verification is still running."
        )
    lines = [
        lead,
        "",
        "**Latest lifecycle:**",
        f"- approval: {state.approval_status}",
        f"- execution: {state.execution_status}",
        f"- verification: {state.verification_status}",
    ]
    if state.latest_summary:
        lines.append(f"- summary: {state.latest_summary}")
    if state.execution_job_id:
        lines.append(f"- execution job: `{state.execution_job_id}`")
    lines.append("")
    lines.append("Say **verify health** or **fetch logs** if you want post-restart evidence.")
    return "\n".join(lines)


def _compose_waiting_approval_reply(state: OperationLifecycleState, text: str) -> str | None:
    if not is_waiting_for_approval(state):
        return None
    if is_blocked_by_credentials(state):
        from aethos_core.runtime.jobs import job_store

        if state.preflight_job_id:
            job = job_store.get(state.preflight_job_id)
            if job:
                pf = dict(job.params.get("mutation_preflight") or {})
                preflight = {**pf, **dict(job.params or {})}
                preflight.setdefault("preflight_status", job.params.get("preflight_status"))
                reply = preflight.get("credential_requirements_reply") or compose_missing_credential_reply(
                    preflight
                )
                if reply:
                    return reply
        return (
            "This restart cannot be approved yet because provider mutation credentials are not configured.\n\n"
            "Configure the provider token in Mission Control → Settings → Provider credentials, "
            "then refresh credentials and re-run preflight."
        )
    if _APPROVAL_FOLLOWUP_RX.search(text):
        from aethos_core.jobs.job_approval_guidance import get_job_approval_guidance, mutation_approval_surface

        if state.preflight_job_id:
            guidance = get_job_approval_guidance(state.preflight_job_id, session_id=state.session_id)
            if guidance.found and guidance.wiring_gap:
                return guidance.wiring_gap
        surface = mutation_approval_surface()
        target = state.target_path()
        return (
            f"Approval is still pending for **{target}**.\n\n"
            f"Open **{surface}**, review blast radius and rollback plan, then approve the governed mutation.\n\n"
            "**No restart has been performed yet.**"
        )
    return None


def compose_lifecycle_followup_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    raw = (text or "").strip()
    if not raw:
        return None

    from aethos_core.providers.github.mutations.rerun_no_execution_followup import (
        compose_rerun_no_execution_followup,
    )

    no_exec = compose_rerun_no_execution_followup(raw, session_id=session_id)
    if no_exec is not None:
        return no_exec

    from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
        route_workflow_discovery_followup,
    )

    workflow_discovery = route_workflow_discovery_followup(raw, session_id=session_id)
    if workflow_discovery is not None:
        return workflow_discovery

    from aethos_core.post_mutation_verification.verification_intent_router import (
        continue_pending_verification_with_target,
        is_post_mutation_verification_intent,
        route_post_mutation_verification,
    )

    continued = continue_pending_verification_with_target(raw, session_id=session_id)
    if continued is not None:
        return continued

    if is_post_mutation_verification_intent(raw, session_id=session_id):
        routed = route_post_mutation_verification(raw, session_id=session_id)
        if routed is not None:
            return routed

    duplicate, dup_state = is_duplicate_mutation_request(raw, session_id=session_id)
    if duplicate and dup_state:
        return (
            compose_duplicate_mutation_reply(dup_state),
            "operation_lifecycle_duplicate_blocked",
            {
                "match_key": dup_state.match_key,
                "execution_job_id": dup_state.execution_job_id or "",
                "preflight_job_id": dup_state.preflight_job_id or "",
            },
        )

    if not is_lifecycle_followup_intent(raw):
        return None

    state = _resolve_state(raw, session_id=session_id)
    if state is None:
        return None

    if has_recent_mutation_execution(state) and not is_blocked_by_credentials(state):
        if _CREDENTIAL_FOLLOWUP_RX.search(raw) or _APPROVAL_FOLLOWUP_RX.search(raw):
            reply = (
                _compose_completed_credential_reply(state)
                if _CREDENTIAL_FOLLOWUP_RX.search(raw)
                else _compose_completed_approval_reply(state)
            )
            return (
                reply,
                "operation_lifecycle_completed_context",
                {
                    "execution_job_id": state.execution_job_id or "",
                    "canonical_state": state.canonical_state,
                },
            )
        if _COMPLETION_FOLLOWUP_RX.search(raw):
            return (
                _compose_completed_approval_reply(state),
                "operation_lifecycle_completion_status",
                {"execution_job_id": state.execution_job_id or ""},
            )

    pending_reply = _compose_waiting_approval_reply(state, raw)
    if pending_reply:
        intent = (
            "credential_requirement_guidance"
            if is_blocked_by_credentials(state)
            else "operation_lifecycle_approval_pending"
        )
        return (
            pending_reply,
            intent,
            {"preflight_job_id": state.preflight_job_id or "", "match_key": state.match_key},
        )

    if _CREDENTIAL_FOLLOWUP_RX.search(raw) and not is_blocked_by_credentials(state):
        return (
            _compose_completed_credential_reply(state),
            "operation_lifecycle_no_credential_block",
            {"match_key": state.match_key},
        )

    return None
