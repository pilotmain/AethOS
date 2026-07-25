# SPDX-License-Identifier: Apache-2.0
"""Vercel project details — API-backed read-only inspection."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.vercel.api_client import find_project_by_name, get_project, parse_project_details


def fetch_project_details(token: str, *, project_name: str) -> dict[str, Any]:
    project = find_project_by_name(token, project_name)
    if not project:
        return {
            "ok": False,
            "source": "provider_api",
            "error": f"Project `{project_name}` not found via Vercel API.",
        }
    project_id = str(project.get("id") or project_name)
    team_id = str(project.get("teamId") or "") or None
    try:
        detail_raw = get_project(token, project_id, team_id=team_id)
    except Exception:
        detail_raw = project
    details = parse_project_details(detail_raw if isinstance(detail_raw, dict) else project)
    return {
        "ok": True,
        "source": "provider_api",
        "project_name": details.get("name") or project_name,
        "details": details,
    }


def format_project_details_output(payload: dict[str, Any]) -> str:
    if not payload.get("ok"):
        return str(payload.get("error") or "Project detail fetch failed.")
    d = payload.get("details") or {}
    lines = [
        f"Project: {payload.get('project_name')}",
        f"- Framework: {d.get('framework') or '—'}",
        f"- Repo: {d.get('repo_link') or '—'}",
        f"- Git provider: {d.get('git_provider') or '—'}",
        f"- Production branch: {d.get('production_branch') or '—'}",
        f"- Node/runtime: {d.get('node_version') or '—'}",
        f"- Root directory: {d.get('root_directory') or '—'}",
        f"- Build command: {d.get('build_command') or '—'}",
        f"- Install command: {d.get('install_command') or '—'}",
        f"- Output directory: {d.get('output_directory') or '—'}",
        f"- Environments: {', '.join(d.get('environments') or []) or '—'}",
        f"- Production URL: {d.get('production_url') or '—'}",
        f"- Latest production state: {d.get('latest_production_state') or 'unknown'}",
    ]
    return "\n".join(lines)
