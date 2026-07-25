# SPDX-License-Identifier: Apache-2.0
"""GitHub Actions enablement and permissions checks."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.github.api_client import request_github
from aethos_core.providers.github.shared.workflow_resolution import resolve_repository


def check_actions_enablement(token: str, *, repository: str) -> dict[str, Any]:
    resolved = resolve_repository(token, repository=repository)
    if not resolved.get("ok"):
        return {
            "ok": False,
            "repository": repository,
            "actions_status": "unknown",
            "error": str(resolved.get("error") or "Repository could not be resolved."),
        }
    owner = str(resolved["owner"])
    repo = str(resolved["repo"])
    full_name = str(resolved["full_name"])

    permissions = request_github(token, "GET", f"/repos/{owner}/{repo}/actions/permissions")
    workflows = request_github(token, "GET", f"/repos/{owner}/{repo}/actions/workflows", params={"per_page": 30})

    actions_enabled: bool | None = None
    allowed_actions = ""
    permission_error = ""
    if permissions.get("ok"):
        data = dict(permissions.get("data") or {})
        actions_enabled = bool(data.get("enabled")) if "enabled" in data else None
        allowed_actions = str(data.get("allowed_actions") or "")
    else:
        permission_error = str(permissions.get("error") or "")
        status = permissions.get("http_status")
        if status in {403, 404}:
            actions_enabled = None

    registered: list[dict[str, Any]] = []
    disabled_count = 0
    workflows_error = ""
    if workflows.get("ok"):
        payload = dict(workflows.get("data") or {})
        for row in payload.get("workflows") or []:
            if not isinstance(row, dict):
                continue
            state = str(row.get("state") or "unknown").lower()
            if state == "disabled":
                disabled_count += 1
            registered.append(
                {
                    "id": row.get("id"),
                    "name": row.get("name"),
                    "path": row.get("path"),
                    "state": state,
                }
            )
    else:
        workflows_error = str(workflows.get("error") or "")

    actions_status = _classify_actions_status(
        actions_enabled=actions_enabled,
        registered_count=len(registered),
        disabled_count=disabled_count,
        permission_error=permission_error,
        workflows_error=workflows_error,
    )

    return {
        "ok": True,
        "repository": full_name,
        "actions_status": actions_status,
        "actions_enabled": actions_enabled,
        "allowed_actions": allowed_actions or None,
        "registered_workflows": registered,
        "registered_workflow_count": len(registered),
        "disabled_workflow_count": disabled_count,
        "permissions_readable": bool(permissions.get("ok")),
        "workflows_api_readable": bool(workflows.get("ok")),
        "permission_error": permission_error or None,
        "workflows_error": workflows_error or None,
    }


def _classify_actions_status(
    *,
    actions_enabled: bool | None,
    registered_count: int,
    disabled_count: int,
    permission_error: str,
    workflows_error: str,
) -> str:
    if actions_enabled is False:
        return "disabled"
    if actions_enabled is True:
        if registered_count and disabled_count == registered_count:
            return "disabled"
        return "enabled"
    if permission_error and ("403" in permission_error or "404" in permission_error):
        return "unknown_permission"
    if workflows_error and ("403" in workflows_error or "404" in workflows_error):
        return "unknown_permission"
    if registered_count:
        return "enabled"
    return "unknown"
