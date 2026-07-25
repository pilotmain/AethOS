# SPDX-License-Identifier: Apache-2.0
"""Vercel REST API client — read-only project listing."""

from __future__ import annotations

from typing import Any

import httpx

VERCEL_API_BASE = "https://api.vercel.com"


class VercelApiError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _request(
    token: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    timeout_sec: float | None = None,
    method: str = "GET",
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from aethos_core.config import get_settings

    timeout = float(timeout_sec if timeout_sec is not None else get_settings().vercel_api_step_timeout_sec)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        with httpx.Client(timeout=timeout) as client:
            if method.upper() == "POST":
                r = client.post(f"{VERCEL_API_BASE}{path}", headers=headers, params=params or {}, json=json_body or {})
            else:
                r = client.get(f"{VERCEL_API_BASE}{path}", headers=headers, params=params or {})
    except httpx.HTTPError as exc:
        raise VercelApiError(f"Vercel API request failed: {exc}") from exc
    if r.status_code == 401:
        raise VercelApiError("Vercel API token is invalid or expired.", status_code=401)
    if r.status_code >= 400:
        raise VercelApiError(
            f"Vercel API returned {r.status_code}: {r.text[:200]}",
            status_code=r.status_code,
        )
    if not r.text.strip():
        return {}
    data = r.json()
    return data if isinstance(data, dict) else {"data": data}


def create_project(
    token: str,
    *,
    name: str,
    git_repo: str | None = None,
    framework: str | None = None,
    team_id: str | None = None,
) -> dict[str, Any]:
    """Create a net-new Vercel project and optionally link a GitHub repository."""
    body: dict[str, Any] = {"name": (name or "").strip()}
    if framework and framework not in {"other", "unknown"}:
        body["framework"] = framework
    repo = (git_repo or "").strip()
    if repo and "/" in repo:
        body["gitRepository"] = {"type": "github", "repo": repo}
    params: dict[str, Any] = {}
    if team_id:
        params["teamId"] = team_id
    return _request(token, "/v10/projects", params=params, method="POST", json_body=body)


def ensure_project_for_greenfield(
    token: str,
    *,
    project_name: str,
    git_repo: str,
    framework: str = "other",
    team_id: str | None = None,
    create_if_missing: bool = True,
) -> dict[str, Any]:
    """Resolve or create a Vercel project for greenfield deployment."""
    existing = find_project_by_name(token, project_name, team_id=team_id)
    if existing:
        return {"ok": True, "created": False, "project": existing}
    if not create_if_missing:
        return {"ok": False, "error": "project_not_found", "project_name": project_name}
    from aethos_core.runtime.operational_environment import assert_environment_allowed

    allowed, detail = assert_environment_allowed(target_environment="staging", operation="Vercel project creation")
    if not allowed:
        return {"ok": False, "error": "environment_blocked", "detail": detail}
    try:
        created = create_project(
            token,
            name=project_name,
            git_repo=git_repo,
            framework=framework,
            team_id=team_id,
        )
    except VercelApiError as exc:
        return {"ok": False, "error": str(exc)}
    return {"ok": True, "created": True, "project": created}


def list_projects(token: str, *, team_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"limit": limit}
    if team_id:
        params["teamId"] = team_id
    data = _request(token, "/v9/projects", params=params)
    projects = data.get("projects")
    if not isinstance(projects, list):
        return []
    return projects


def find_project_by_name(
    token: str,
    name: str,
    *,
    team_id: str | None = None,
) -> dict[str, Any] | None:
    target = (name or "").strip().lower()
    if not target:
        return None
    for item in list_projects(token, team_id=team_id, limit=100):
        if str(item.get("name") or "").strip().lower() == target:
            return item
    return None


def get_project(
    token: str,
    project_id_or_name: str,
    *,
    team_id: str | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if team_id:
        params["teamId"] = team_id
    return _request(token, f"/v9/projects/{project_id_or_name}", params=params)


def list_deployments(
    token: str,
    *,
    project_id: str,
    team_id: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"projectId": project_id, "limit": limit}
    if team_id:
        params["teamId"] = team_id
    data = _request(token, "/v6/deployments", params=params)
    deployments = data.get("deployments")
    if not isinstance(deployments, list):
        return []
    return deployments


def list_project_domains(
    token: str,
    project_id: str,
    *,
    team_id: str | None = None,
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {}
    if team_id:
        params["teamId"] = team_id
    data = _request(token, f"/v9/projects/{project_id}/domains", params=params)
    domains = data.get("domains")
    if not isinstance(domains, list):
        return []
    return domains


def get_deployment_events(
    token: str,
    deployment_id: str,
    *,
    limit: int = 100,
) -> list[dict[str, Any]]:
    data = _request(
        token,
        f"/v2/deployments/{deployment_id}/events",
        params={"limit": limit, "direction": "backward"},
    )
    events = data if isinstance(data, list) else data.get("events")
    if not isinstance(events, list):
        return []
    return events


def parse_deployment_record(item: dict[str, Any]) -> dict[str, Any]:
    meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
    return {
        "id": str(item.get("uid") or item.get("id") or ""),
        "name": str(item.get("name") or ""),
        "url": str(item.get("url") or ""),
        "state": str(item.get("readyState") or item.get("state") or "unknown").lower(),
        "target": str(item.get("target") or item.get("deploymentTarget") or "unknown").lower(),
        "branch": str(meta.get("githubCommitRef") or meta.get("gitlabCommitRef") or meta.get("branch") or ""),
        "commit": str(meta.get("githubCommitSha") or meta.get("gitlabCommitSha") or meta.get("commit") or "")[:12],
        "commit_message": str(meta.get("githubCommitMessage") or meta.get("gitlabCommitMessage") or "")[:200],
        "created_at": item.get("createdAt") or item.get("created"),
        "building_at": item.get("buildingAt"),
        "ready_at": item.get("ready") or item.get("readyAt"),
        "error_message": str(item.get("errorMessage") or item.get("error") or ""),
        "inspector_url": str(item.get("inspectorUrl") or ""),
    }


def parse_domain_record(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "domain": str(item.get("name") or item.get("domain") or ""),
        "type": str(item.get("type") or "custom"),
        "verified": bool(item.get("verified")),
        "production": bool(item.get("production") or item.get("gitBranch") == "production"),
        "redirect": str(item.get("redirect") or item.get("redirectStatusCode") or ""),
        "last_seen": item.get("updatedAt") or item.get("createdAt"),
        "apex": str(item.get("apexName") or ""),
    }


def parse_project_details(item: dict[str, Any]) -> dict[str, Any]:
    base = parse_project_record(item)
    link = item.get("link") if isinstance(item.get("link"), dict) else {}
    envs = item.get("env") if isinstance(item.get("env"), list) else []
    return {
        **base,
        "git_provider": str(link.get("type") or link.get("gitCredentialId") or ""),
        "production_branch": str(link.get("productionBranch") or item.get("productionBranch") or ""),
        "root_directory": str(item.get("rootDirectory") or ""),
        "build_command": str(item.get("buildCommand") or ""),
        "dev_command": str(item.get("devCommand") or ""),
        "install_command": str(item.get("installCommand") or ""),
        "output_directory": str(item.get("outputDirectory") or ""),
        "node_version": str(item.get("nodeVersion") or ""),
        "environment_count": len(envs),
        "environments": [str(e.get("key") or e.get("type") or "") for e in envs if isinstance(e, dict)][:12],
    }


def parse_project_record(item: dict[str, Any]) -> dict[str, Any]:
    """Structured API project model for inventory and reports."""
    name = str(item.get("name") or "").strip()
    link = item.get("link") if isinstance(item.get("link"), dict) else {}
    repo = ""
    if link:
        org = str(link.get("org") or link.get("owner") or "")
        repo_name = str(link.get("repo") or "")
        if org and repo_name:
            repo = f"{org}/{repo_name}"
        elif repo_name:
            repo = repo_name

    targets = item.get("targets") if isinstance(item.get("targets"), dict) else {}
    target_names = sorted(str(k) for k in targets.keys())
    domains: list[str] = []
    production_url = None
    prod = targets.get("production")
    if isinstance(prod, dict):
        alias = prod.get("alias")
        if isinstance(alias, list) and alias:
            domains.extend(str(a) for a in alias if a)
            production_url = str(alias[0])
        elif isinstance(alias, str) and alias:
            domains.append(alias)
            production_url = alias
        if not production_url and prod.get("url"):
            production_url = str(prod.get("url"))

    latest_deployments = item.get("latestDeployments")
    latest_deployment = None
    latest_production_state = "unknown"
    latest_preview_state = "unknown"
    if isinstance(latest_deployments, list):
        for dep in latest_deployments:
            if not isinstance(dep, dict):
                continue
            target = str(dep.get("target") or dep.get("deploymentTarget") or "").lower()
            state = str(dep.get("readyState") or dep.get("state") or "unknown").lower()
            if target == "production":
                latest_production_state = state
                latest_deployment = dep
            elif target in ("preview", "staging"):
                latest_preview_state = state
            if latest_deployment is None:
                latest_deployment = dep

    return {
        "name": name,
        "id": str(item.get("id") or ""),
        "framework": str(item.get("framework") or item.get("nodeVersion") or ""),
        "account_id": str(item.get("accountId") or ""),
        "team_id": str(item.get("teamId") or ""),
        "latest_deployment": latest_deployment,
        "latest_production_state": latest_production_state,
        "latest_preview_state": latest_preview_state,
        "targets": target_names,
        "domains": domains,
        "production_url": production_url,
        "repo_link": repo,
        "created_at": item.get("createdAt"),
        "updated_at": item.get("updatedAt"),
    }


def test_connection(token: str) -> dict[str, Any]:
    projects = list_projects(token, limit=5)
    names = [str(p.get("name") or "") for p in projects if p.get("name")]
    return {
        "ok": True,
        "project_count": len(projects),
        "sample_projects": names[:5],
    }
