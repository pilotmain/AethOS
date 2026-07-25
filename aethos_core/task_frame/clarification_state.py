# SPDX-License-Identifier: Apache-2.0
"""Clarification state — store pending target selection tasks."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import Any

from aethos_core.task_frame.task_expiration import task_expires_at
from aethos_core.task_frame.task_frame import TaskCandidate, TaskFrame
from aethos_core.task_frame.task_memory import save_task_frame


def _candidate_from_row(idx: int, row: dict[str, Any]) -> TaskCandidate:
    project = str(row.get("project_name") or row.get("project") or "")
    environment = str(row.get("environment") or "production")
    service = str(row.get("service_name") or row.get("service") or row.get("name") or "")
    path = row.get("path") or f"{project} / {environment} / {service}"
    return TaskCandidate(
        index=idx,
        project=project,
        environment=environment,
        service=service,
        service_id=row.get("service_id"),
        path=str(path),
        raw=dict(row),
    )


def store_target_selection_task(
    *,
    session_id: str,
    provider: str,
    operation: str,
    original_request: str,
    candidates: list[dict[str, Any]],
    params: dict[str, Any] | None = None,
) -> TaskFrame:
    now = datetime.now(UTC).isoformat()
    task_id = f"tf-{secrets.token_hex(6)}"
    numbered = [_candidate_from_row(idx, row) for idx, row in enumerate(candidates[:8], start=1)]
    frame = TaskFrame(
        session_id=session_id,
        task_id=task_id,
        intent="provider_restart" if operation == "restart" else f"provider_{operation}",
        provider=provider,
        operation=operation,
        status="awaiting_target_selection",
        candidates=numbered,
        next_action="create_mutation_preflight_after_selection",
        original_request=original_request,
        params=dict(params or {}),
        created_at=now,
        updated_at=now,
        expires_at=task_expires_at(),
    )
    save_task_frame(frame)
    return frame


def candidates_from_target_resolution(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(candidates[:8], start=1):
        project = str(row.get("project_name") or row.get("project") or "")
        environment = str(row.get("environment") or "production")
        service = str(row.get("service_name") or row.get("service") or row.get("name") or "")
        path = row.get("path") or f"{project} / {environment} / {service}"
        rows.append({**row, "index": idx, "path": path})
    return rows
