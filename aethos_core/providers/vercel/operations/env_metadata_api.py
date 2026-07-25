# SPDX-License-Identifier: Apache-2.0
"""Vercel env var metadata — keys and targets only, never secret values."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.vercel.api_client import find_project_by_name, get_project


def fetch_env_metadata(token: str, *, project_name: str) -> dict[str, Any]:
    project = find_project_by_name(token, project_name)
    if not project:
        return {"ok": False, "error": f"Project `{project_name}` not found via Vercel API."}
    project_id = str(project.get("id") or "")
    team_id = str(project.get("teamId") or "") or None
    try:
        detail_raw = get_project(token, project_id, team_id=team_id)
    except Exception:
        detail_raw = project
    detail = detail_raw if isinstance(detail_raw, dict) else project
    envs = detail.get("env") if isinstance(detail.get("env"), list) else []
    metadata: list[dict[str, str]] = []
    for item in envs:
        if not isinstance(item, dict):
            continue
        metadata.append(
            {
                "key": str(item.get("key") or ""),
                "target": ",".join(str(t) for t in (item.get("target") or []) if t) or str(item.get("type") or ""),
                "git_branch": str(item.get("gitBranch") or ""),
                "id": str(item.get("id") or ""),
            }
        )
    return {
        "ok": True,
        "project_name": project_name,
        "env_count": len(metadata),
        "env_metadata": metadata,
        "note": "Metadata only — secret values are never returned.",
    }


def format_env_metadata_output(payload: dict[str, Any]) -> str:
    if not payload.get("ok"):
        return str(payload.get("error") or "Env metadata fetch failed.")
    lines = [
        f"Env metadata for **{payload.get('project_name')}** ({payload.get('env_count', 0)} vars):",
    ]
    for item in payload.get("env_metadata") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('key')}` target={item.get('target') or '—'}")
    lines.append("")
    lines.append(str(payload.get("note") or "Metadata only."))
    return "\n".join(lines)
