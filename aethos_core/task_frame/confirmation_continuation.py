# SPDX-License-Identifier: Apache-2.0
"""Map confirmation phrases to pending operational actions."""

from __future__ import annotations

import re

from typing import Any

from aethos_core.task_frame.pending_action import PendingAction, clear_pending_action, get_pending_action

_ACTION_CONFIRM_RX = re.compile(
    r"\b("
    r"please\s+do"
    r"|go\s+ahead"
    r"|do\s+it"
    r"|continue"
    r"|retry\s+now"
    r"|create\s+the\s+preflight"
    r"|yes(?:\s+please)?"
    r")\b",
    re.I,
)


def is_action_confirmation(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if is_binding_update_confirmation(raw):
        return False
    return bool(_ACTION_CONFIRM_RX.search(raw))


def is_binding_update_confirmation(text: str) -> bool:
    return bool(
        re.search(
            r"\b(yes\s+update(?:\s+it)?|update\s+the\s+binding|use\s+that\s+repo|confirm)\b",
            text or "",
            re.I,
        )
    )


def compose_pending_action_continuation_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_action_confirmation(text):
        return None
    action = get_pending_action(session_id=session_id)
    if action is None:
        return None
    if action.next_action == "create_mutation_preflight":
        return create_governed_retry_preflight(action, session_id=session_id)
    return None


def create_governed_retry_preflight(
    action: PendingAction,
    *,
    session_id: str,
) -> tuple[str, str, dict[str, str]]:
    from aethos_core.jobs.job_approval_guidance import mutation_approval_surface
    from aethos_core.operations.mutations.taxonomy import CANONICAL_MUTATION_PREFLIGHT_JOB_TYPE
    from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_preflight
    from aethos_core.provider_topology.source_binding_resolver import refresh_params_source_binding
    from aethos_core.runtime.authority import authority
    from aethos_core.task_frame.pending_action import clear_pending_action

    op = action.operation.replace("_", " ")
    user_request = f"restart railway {action.service} service"
    params: dict[str, Any] = {
        "user_request": user_request,
        "provider": action.provider,
        "operation_type": action.operation,
        "target_name": action.service,
        "target": {
            "provider": action.provider,
            "project_name": action.project,
            "environment": action.environment,
            "service_name": action.service,
            "resolved": True,
            "source": "retry_active_operation",
        },
        "target_resolved": True,
        "target_status": "resolved",
        **dict(action.params or {}),
    }
    params, resolution, _regression = refresh_params_source_binding(params, session_id=session_id)

    target = dict(params.get("target") or {})
    if resolution.service_id:
        target["service_id"] = resolution.service_id
        params["target"] = target

    job = authority.create_job(
        title=f"{action.provider.title()} {op} mutation preflight",
        job_type=CANONICAL_MUTATION_PREFLIGHT_JOB_TYPE,
        params=params,
        source="retry_active_operation",
        session_id=session_id,
        auto_run=True,
    )
    sync_thread_from_preflight(job=job, user_request=user_request)
    clear_pending_action(session_id=session_id)
    path = action.service_path()
    binding_repo = resolution.github_repo or action.source_binding
    binding_line = f" using the corrected source binding **{binding_repo}**" if binding_repo else ""
    body = (
        f"Got it — creating a new governed Railway **{op}** preflight for **{path}**{binding_line}.\n\n"
        f"I created governed preflight `{job.id}`. **No {op} has been performed yet.**\n\n"
        f"Review it in **{mutation_approval_surface()}**, then approve if the blast radius and rollback plan look correct."
    )
    return (
        body,
        "pending_action_preflight_created",
        {
            "proposed_job_id": job.id,
            "provider": action.provider,
            "operation": action.operation,
            "service": action.service,
            "source_binding": str(binding_repo or ""),
        },
    )


def _create_preflight_from_pending(
    action: PendingAction,
    *,
    session_id: str,
) -> tuple[str, str, dict[str, str]]:
    return create_governed_retry_preflight(action, session_id=session_id)
