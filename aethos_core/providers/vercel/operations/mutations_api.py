# SPDX-License-Identifier: Apache-2.0
"""Vercel governed mutations — redeploy (approval-gated)."""

from __future__ import annotations

from typing import Any

import httpx

from aethos_core.providers.vercel.api_client import VERCEL_API_BASE, find_project_by_name
from aethos_core.security.secret_redaction import redact_text


def redeploy_project(token: str, *, target_name: str, team_id: str | None = None) -> dict[str, Any]:
    project = find_project_by_name(token, target_name, team_id=team_id)
    if not project:
        return {"ok": False, "detail": f"Vercel project `{target_name}` not found."}
    project_id = str(project.get("id") or "")
    if not project_id:
        return {"ok": False, "detail": "Project id unavailable."}

    params: dict[str, str] = {}
    if team_id:
        params["teamId"] = team_id
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"name": target_name, "project": project_id, "target": "production"}
    try:
        with httpx.Client(timeout=45.0) as client:
            r = client.post(f"{VERCEL_API_BASE}/v13/deployments", headers=headers, params=params, json=body)
        if r.status_code >= 400:
            return {"ok": False, "detail": redact_text(r.text[:240] or f"HTTP {r.status_code}")}
        data = r.json() if r.content else {}
        deployment_id = str(data.get("id") or "")
        return {
            "ok": True,
            "detail": f"Production redeploy triggered for `{target_name}`.",
            "project_id": project_id,
            "deployment_id": deployment_id or None,
            "operation": "redeploy",
        }
    except httpx.HTTPError as exc:
        return {"ok": False, "detail": redact_text(str(exc))}


def deploy_project_from_github(
    token: str,
    *,
    target_name: str,
    repo: str,
    ref: str = "main",
    github_repo_id: int | str | None = None,
    team_id: str | None = None,
    target: str = "production",
) -> dict[str, Any]:
    """Trigger a fresh Vercel deployment from a connected GitHub repository."""
    project = find_project_by_name(token, target_name, team_id=team_id)
    if not project:
        return {"ok": False, "detail": f"Vercel project `{target_name}` not found."}
    project_id = str(project.get("id") or "")
    if not project_id:
        return {"ok": False, "detail": "Project id unavailable."}

    git_source: dict[str, Any] = {"type": "github", "ref": ref}
    if github_repo_id:
        git_source["repoId"] = int(github_repo_id)
    else:
        slug = (repo or "").strip()
        if "/" in slug:
            git_source["org"] = slug.split("/", 1)[0]
            git_source["repo"] = slug.split("/", 1)[1]

    params: dict[str, str] = {}
    if team_id:
        params["teamId"] = team_id
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {
        "name": target_name,
        "project": project_id,
        "target": target,
        "gitSource": git_source,
    }
    try:
        with httpx.Client(timeout=60.0) as client:
            r = client.post(f"{VERCEL_API_BASE}/v13/deployments", headers=headers, params=params, json=body)
        if r.status_code >= 400:
            return {"ok": False, "detail": redact_text(r.text[:240] or f"HTTP {r.status_code}")}
        data = r.json() if r.content else {}
        deployment_id = str(data.get("id") or "")
        url = str(data.get("url") or data.get("alias") or "")
        if url and not url.startswith("http"):
            url = f"https://{url}"
        return {
            "ok": True,
            "detail": f"GitHub deployment triggered for `{target_name}` @ `{ref}`.",
            "project_id": project_id,
            "deployment_id": deployment_id or None,
            "deployment_url": url or None,
            "operation": "deploy_from_github",
        }
    except httpx.HTTPError as exc:
        return {"ok": False, "detail": redact_text(str(exc))}


_IN_FLIGHT_DEPLOYMENT_STATES = frozenset({"BUILDING", "QUEUED", "INITIALIZING", "DEPLOYING"})


def _resolve_vercel_team_id(*, project: dict[str, Any], team_id: str | None = None) -> str | None:
    from aethos_core.config import get_settings

    explicit = (team_id or "").strip()
    if explicit:
        return explicit
    from_project = str(project.get("teamId") or "").strip()
    if from_project:
        return from_project
    from_settings = str(get_settings().vercel_team_id or "").strip()
    return from_settings or None


def unpause_project(
    token: str,
    *,
    project_id: str,
    target_name: str,
    team_id: str | None = None,
) -> dict[str, Any]:
    """Resume a paused Vercel project."""
    params: dict[str, str] = {}
    resolved_team = (team_id or "").strip()
    if resolved_team:
        params["teamId"] = resolved_team
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        with httpx.Client(timeout=45.0) as client:
            r = client.post(
                f"{VERCEL_API_BASE}/v1/projects/{project_id}/unpause",
                headers=headers,
                params=params or None,
            )
        if r.status_code >= 400:
            return {"ok": False, "detail": redact_text(r.text[:240] or f"HTTP {r.status_code}")}
        return {
            "ok": True,
            "detail": f"Unpaused Vercel project `{target_name}`.",
            "project_id": project_id,
            "operation": "unpause",
        }
    except httpx.HTTPError as exc:
        return {"ok": False, "detail": redact_text(str(exc))}


def pause_project(
    token: str,
    *,
    project_id: str,
    target_name: str,
    team_id: str | None = None,
) -> dict[str, Any]:
    """Pause a Vercel project — production returns 503 until unpaused."""
    params: dict[str, str] = {}
    resolved_team = (team_id or "").strip()
    if resolved_team:
        params["teamId"] = resolved_team
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        with httpx.Client(timeout=45.0) as client:
            r = client.post(
                f"{VERCEL_API_BASE}/v1/projects/{project_id}/pause",
                headers=headers,
                params=params or None,
            )
        if r.status_code >= 400:
            return {"ok": False, "detail": redact_text(r.text[:240] or f"HTTP {r.status_code}")}
        return {
            "ok": True,
            "detail": f"Paused Vercel project `{target_name}` — production serves 503 until unpaused.",
            "project_id": project_id,
            "operation": "stop",
            "stop_method": "project_pause",
        }
    except httpx.HTTPError as exc:
        return {"ok": False, "detail": redact_text(str(exc))}


def stop_project(token: str, *, target_name: str, team_id: str | None = None) -> dict[str, Any]:
    """Stop Vercel compute: cancel in-flight builds, or pause live production."""
    from aethos_core.providers.vercel.api_client import list_deployments

    project = find_project_by_name(token, target_name, team_id=team_id)
    if not project:
        settings_team = _resolve_vercel_team_id(project={}, team_id=team_id)
        if settings_team and settings_team != team_id:
            project = find_project_by_name(token, target_name, team_id=settings_team)
    if not project:
        return {
            "ok": False,
            "detail": (
                f"Vercel project `{target_name}` not found. "
                "Register it in deployment targets with `vercel_project` and ensure VERCEL_TEAM_ID if team-scoped."
            ),
        }
    project_id = str(project.get("id") or "")
    resolved_team_id = _resolve_vercel_team_id(project=project, team_id=team_id)
    deployments = list_deployments(token, project_id=project_id, team_id=resolved_team_id, limit=8)
    in_flight = None
    for row in deployments:
        state = str(row.get("state") or row.get("readyState") or "").upper()
        if state in _IN_FLIGHT_DEPLOYMENT_STATES:
            in_flight = row
            break
    if in_flight is not None:
        deployment_id = str(in_flight.get("uid") or in_flight.get("id") or "")
        if not deployment_id:
            return {"ok": False, "detail": "In-flight deployment id unavailable."}
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        params: dict[str, str] = {}
        if resolved_team_id:
            params["teamId"] = resolved_team_id
        try:
            with httpx.Client(timeout=45.0) as client:
                r = client.patch(
                    f"{VERCEL_API_BASE}/v12/deployments/{deployment_id}/cancel",
                    headers=headers,
                    params=params or None,
                )
            if r.status_code >= 400:
                return {"ok": False, "detail": redact_text(r.text[:240] or f"HTTP {r.status_code}")}
            return {
                "ok": True,
                "detail": f"Cancelled in-flight deployment `{deployment_id}` on `{target_name}`.",
                "project_id": project_id,
                "deployment_id": deployment_id,
                "operation": "stop",
                "stop_method": "deployment_cancel",
            }
        except httpx.HTTPError as exc:
            return {"ok": False, "detail": redact_text(str(exc))}

    return pause_project(
        token,
        project_id=project_id,
        target_name=target_name,
        team_id=resolved_team_id,
    )


def upsert_env_var(
    token: str,
    *,
    target_name: str,
    key: str,
    value: str,
    targets: list[str] | None = None,
    team_id: str | None = None,
) -> dict[str, Any]:
    """Create or update a Vercel env var under approval — never log raw value in responses."""
    project = find_project_by_name(token, target_name, team_id=team_id)
    if not project:
        return {"ok": False, "detail": f"Vercel project `{target_name}` not found."}
    project_id = str(project.get("id") or "")
    env_key = str(key or "").strip()
    if not env_key:
        return {"ok": False, "detail": "Env var key required."}
    if not str(value or "").strip():
        return {"ok": False, "detail": "Env var value required (supplied via secure preflight reference)."}
    params: dict[str, str] = {}
    if team_id:
        params["teamId"] = team_id
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {
        "key": env_key,
        "value": value,
        "type": "encrypted",
        "target": targets or ["production", "preview", "development"],
    }
    try:
        with httpx.Client(timeout=45.0) as client:
            r = client.post(
                f"{VERCEL_API_BASE}/v10/projects/{project_id}/env",
                headers=headers,
                params=params,
                json=body,
            )
        if r.status_code >= 400:
            return {"ok": False, "detail": redact_text(r.text[:240] or f"HTTP {r.status_code}")}
        return {
            "ok": True,
            "detail": f"Env var `{env_key}` upserted for `{target_name}`.",
            "project_id": project_id,
            "env_key": env_key,
            "operation": "set_env_var",
        }
    except httpx.HTTPError as exc:
        return {"ok": False, "detail": redact_text(str(exc))}


def remove_env_var(
    token: str,
    *,
    target_name: str,
    key: str,
    team_id: str | None = None,
) -> dict[str, Any]:
    """Remove a Vercel env var by key."""
    from aethos_core.providers.vercel.operations.env_metadata_api import fetch_env_metadata

    meta = fetch_env_metadata(token, project_name=target_name)
    if not meta.get("ok"):
        return {"ok": False, "detail": str(meta.get("error") or "Project env metadata unavailable.")}
    env_key = str(key or "").strip()
    env_id = None
    for item in meta.get("env_metadata") or []:
        if str(item.get("key") or "") == env_key:
            env_id = str(item.get("id") or "")
            break
    if not env_id:
        return {"ok": False, "detail": f"Env var `{env_key}` not found on `{target_name}`."}
    project = find_project_by_name(token, target_name, team_id=team_id)
    project_id = str((project or {}).get("id") or "")
    params: dict[str, str] = {}
    if team_id:
        params["teamId"] = team_id
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with httpx.Client(timeout=45.0) as client:
            r = client.delete(
                f"{VERCEL_API_BASE}/v9/projects/{project_id}/env/{env_id}",
                headers=headers,
                params=params,
            )
        if r.status_code >= 400:
            return {"ok": False, "detail": redact_text(r.text[:240] or f"HTTP {r.status_code}")}
        return {
            "ok": True,
            "detail": f"Env var `{env_key}` removed from `{target_name}`.",
            "operation": "remove_env_var",
        }
    except httpx.HTTPError as exc:
        return {"ok": False, "detail": redact_text(str(exc))}
