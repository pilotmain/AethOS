# SPDX-License-Identifier: Apache-2.0
"""Vercel deployments — API-backed read-only inspection."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.vercel.api_client import (
    find_project_by_name,
    list_deployments,
    parse_deployment_record,
)


def fetch_deployments(
    token: str,
    *,
    project_name: str,
    limit: int = 20,
) -> dict[str, Any]:
    project = find_project_by_name(token, project_name)
    if not project:
        return {
            "ok": False,
            "source": "provider_api",
            "error": f"Project `{project_name}` not found via Vercel API.",
            "deployments": [],
        }
    project_id = str(project.get("id") or "")
    team_id = str(project.get("teamId") or "") or None
    raw = list_deployments(token, project_id=project_id, team_id=team_id, limit=limit)
    records = [parse_deployment_record(d) for d in raw if isinstance(d, dict)]
    return {
        "ok": True,
        "source": "provider_api",
        "project_id": project_id,
        "project_name": str(project.get("name") or project_name),
        "deployment_count": len(records),
        "deployments": records,
    }


def format_deployments_output(payload: dict[str, Any]) -> str:
    if not payload.get("ok"):
        return str(payload.get("error") or "Deployment fetch failed.")
    lines = [
        f"Project: {payload.get('project_name')}",
        f"Deployments ({payload.get('deployment_count', 0)}):",
        "",
    ]
    for dep in payload.get("deployments") or []:
        lines.append(
            f"- **{dep.get('state', 'unknown')}** · {dep.get('target', 'unknown')} · "
            f"`{dep.get('id', '')[:12]}` · branch `{dep.get('branch') or '—'}` · "
            f"commit `{dep.get('commit') or '—'}` · {dep.get('created_at') or '—'}"
        )
        if dep.get("error_message"):
            lines.append(f"  - error: {dep['error_message'][:240]}")
        if dep.get("commit_message"):
            lines.append(f"  - message: {dep['commit_message'][:160]}")
    if len(lines) <= 3:
        lines.append("(no deployments returned)")
    return "\n".join(lines)
