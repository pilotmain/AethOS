# SPDX-License-Identifier: Apache-2.0
"""Task continuation — route next user turn into active operational task."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.jobs.job_approval_guidance import mutation_approval_surface
from aethos_core.operations.mutations.taxonomy import CANONICAL_MUTATION_PREFLIGHT_JOB_TYPE
from aethos_core.runtime.authority import authority
from aethos_core.task_frame.selection_resolver import resolve_selections, selection_error_message
from aethos_core.task_frame.task_memory import complete_task_frame, get_active_task_frame

_EXECUTION_ACK_RX = re.compile(
    r"\b("
    r"redeploy(?:ing)?(?:\s+with\s+latest\s+changes)?"
    r"|deploy(?:ing)?(?:\s+latest)?"
    r"|yes(?:\s+please)?"
    r"|go\s+ahead"
    r"|do\s+it"
    r"|continue"
    r"|proceed"
    r")\b",
    re.I,
)


def is_task_execution_ack(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    return bool(_EXECUTION_ACK_RX.search(raw))


def compose_task_continuation_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    frame = get_active_task_frame(session_id=session_id)
    if frame is None:
        return None
    if frame.status != "awaiting_target_selection":
        return None

    selected = resolve_selections(text, frame)
    if not selected and is_task_execution_ack(text):
        from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
            safe_run_deployment_readiness_checks,
        )
        from aethos_core.providers.railway.railway_inventory_target_picker import pick_railway_targets

        checks = safe_run_deployment_readiness_checks(
            user_text=frame.original_request,
            session_id=session_id,
        )
        picked = pick_railway_targets(checks, frame.original_request)
        if picked.targets:
            selected = [
                _candidate_from_target(row, index=idx)
                for idx, row in enumerate(picked.targets, start=1)
            ]

    if not selected:
        return (
            selection_error_message(frame),
            "task_frame_selection_invalid",
            {"task_id": frame.task_id, "provider": frame.provider},
        )

    if frame.next_action == "create_mutation_preflight_after_selection":
        if len(selected) == 1:
            return _create_preflight_after_selection(frame, selected[0], session_id=session_id)
        return _create_preflights_after_selection(frame, selected, session_id=session_id)

    return None


def _candidate_from_target(row, *, index: int):
    from aethos_core.task_frame.task_frame import TaskCandidate

    return TaskCandidate(
        index=index,
        project=row.project,
        environment=row.environment,
        service=row.service,
        path=row.path,
    )


def _create_preflight_after_selection(
    frame,
    selected,
    *,
    session_id: str,
) -> tuple[str, str, dict[str, str]]:
    path = selected.path or f"{selected.project} / {selected.environment} / {selected.service}"
    target = {
        "provider": frame.provider,
        "service_name": selected.service,
        "project_name": selected.project,
        "environment": selected.environment,
        "service_id": selected.service_id,
        "confidence": 0.98,
        "resolved": True,
        "source": "task_frame_selection",
    }
    params = {
        **dict(frame.params or {}),
        "user_request": frame.original_request,
        "provider": frame.provider,
        "operation_type": frame.operation,
        "target_name": selected.service,
        "target": target,
        "target_resolved": True,
        "target_status": "resolved",
        "task_frame_id": frame.task_id,
        "selected_target_path": path,
    }
    op = frame.operation.replace("_", " ")
    title = f"{frame.provider.title()} {op} mutation preflight"
    job = authority.create_job(
        title=title,
        job_type=CANONICAL_MUTATION_PREFLIGHT_JOB_TYPE,
        params=params,
        source="chat",
        session_id=session_id,
        auto_run=True,
    )
    from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_preflight

    sync_thread_from_preflight(job=job, user_request=frame.original_request)
    complete_task_frame(session_id=session_id, status="completed")
    approval_path = mutation_approval_surface()
    body = (
        f"Got it — selected Railway target **{path}**.\n\n"
        f"I created a governed {op} preflight `{job.id}`. **No {op} has been performed yet.**\n\n"
        f"Review it in **{approval_path}** before approving execution."
    )
    return (
        body,
        "task_frame_preflight_created",
        {
            "task_id": frame.task_id,
            "proposed_job_id": job.id,
            "provider": frame.provider,
            "operation_type": frame.operation,
            "target_name": selected.service,
            "selected_target_path": path,
        },
    )


def _create_preflights_after_selection(
    frame,
    selected,
    *,
    session_id: str,
) -> tuple[str, str, dict[str, str]]:
    from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_preflight

    op = frame.operation.replace("_", " ")
    job_ids: list[str] = []
    paths: list[str] = []
    for candidate in selected:
        path = candidate.path or f"{candidate.project} / {candidate.environment} / {candidate.service}"
        target = {
            "provider": frame.provider,
            "service_name": candidate.service,
            "project_name": candidate.project,
            "environment": candidate.environment,
            "service_id": candidate.service_id,
            "confidence": 0.98,
            "resolved": True,
            "source": "task_frame_selection",
        }
        params = {
            **dict(frame.params or {}),
            "user_request": frame.original_request,
            "provider": frame.provider,
            "operation_type": frame.operation,
            "target_name": candidate.service,
            "target": target,
            "target_resolved": True,
            "target_status": "resolved",
            "task_frame_id": frame.task_id,
            "selected_target_path": path,
        }
        title = f"{frame.provider.title()} {op} mutation preflight — {candidate.service}"
        job = authority.create_job(
            title=title,
            job_type=CANONICAL_MUTATION_PREFLIGHT_JOB_TYPE,
            params=params,
            source="chat",
            session_id=session_id,
            auto_run=True,
        )
        sync_thread_from_preflight(job=job, user_request=frame.original_request)
        job_ids.append(job.id)
        paths.append(path)

    complete_task_frame(session_id=session_id, status="completed")
    approval_path = mutation_approval_surface()
    listed = "\n".join(f"- `{job_id}` → **{path}**" for job_id, path in zip(job_ids, paths))
    body = (
        f"Got it — selected **{len(paths)}** Railway target(s) for **{op}**:\n"
        f"{listed}\n\n"
        f"I created governed {op} prefights for each target. **No {op} has been performed yet.**\n\n"
        f"Review them in **{approval_path}** before approving execution."
    )
    return (
        body,
        "task_frame_preflight_created",
        {
            "task_id": frame.task_id,
            "proposed_job_id": job_ids[0] if job_ids else "",
            "proposed_job_ids": ",".join(job_ids),
            "provider": frame.provider,
            "operation_type": frame.operation,
            "selected_target_paths": " | ".join(paths),
            "target_count": str(len(paths)),
        },
    )


def has_active_task_frame(*, session_id: str) -> bool:
    return get_active_task_frame(session_id=session_id) is not None
