# SPDX-License-Identifier: Apache-2.0
"""Persist pending Railway deploy/redeploy target selection after ambiguous inventory."""

from __future__ import annotations

from typing import Any

from aethos_core.task_frame.clarification_state import (
    candidates_from_target_resolution,
    store_target_selection_task,
)
from aethos_core.task_frame.task_frame import TaskFrame


def detect_railway_deploy_operation(user_text: str) -> str:
    lower = (user_text or "").lower()
    if "restart" in lower:
        return "restart"
    return "redeploy"


def store_railway_deploy_selection_task(
    *,
    session_id: str,
    user_text: str,
    checks: dict[str, Any],
    candidates: list[dict[str, Any]],
    operation: str | None = None,
    params: dict[str, Any] | None = None,
) -> TaskFrame:
    op = operation or detect_railway_deploy_operation(user_text)
    numbered = candidates_from_target_resolution(list(candidates or []))
    merged_params = {
        "provider": "railway",
        "operation_type": op,
        **dict(params or {}),
    }
    return store_target_selection_task(
        session_id=session_id,
        provider="railway",
        operation=op,
        original_request=user_text,
        candidates=numbered,
        params=merged_params,
    )


def compose_ambiguous_railway_target_reply(
    *,
    operation: str,
    candidates: list[dict[str, Any]],
) -> str:
    op = operation.replace("_", " ")
    lines = [
        f"Railway service targeting is ambiguous for **{op}**.",
        "",
        "Specify the environment and service(s), for example:",
        "- `staging: aethos-api, aethos-ui`",
        "- `pilotos / staging / aethos-api`",
        "",
        "Matching services:",
    ]
    for idx, row in enumerate(candidates[:8], start=1):
        path = row.get("path") or (
            f"{row.get('project_name')} / {row.get('environment')} / {row.get('service_name')}"
        )
        lines.append(f"{idx}. {path}")
    lines.extend(
        [
            "",
            "Safe next command: `show Railway projects`",
            "",
            "No mutation preflight has been created yet.",
        ]
    )
    return "\n".join(lines)
