# SPDX-License-Identifier: Apache-2.0
"""Resolve greenfield deployment source from remote GitHub repo (no local workspace required)."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.deployment_targets.resolver import resolve_deployment_target

_PROJECT_NAME_RX = re.compile(
    r"\b(?:project|app|service)\s+[`'\"]?([a-z0-9][a-z0-9._-]+)[`'\"]?\b",
    re.I,
)


def infer_project_name_from_text(text: str, *, repo: str, deployment_target: dict[str, Any] | None = None) -> str:
    if deployment_target and deployment_target.get("vercel_project"):
        return str(deployment_target["vercel_project"]).strip().lower()
    raw = (text or "").strip()
    match = _PROJECT_NAME_RX.search(raw)
    if match:
        return match.group(1).strip().lower()
    from aethos_core.providers.railway.greenfield_deployment.git_remote_resolution import normalize_github_repository_slug

    repo_slug = normalize_github_repository_slug(repo)
    if repo_slug and "/" in repo_slug:
        return repo_slug.split("/")[-1]
    return repo_slug.split("/")[-1] if repo_slug else "app"


def resolve_remote_github_repo_from_text(
    user_text: str,
    *,
    session_id: str = "default",
    workspace_hint: str = "",
    user_id: str = "",
    channel: str = "web",
) -> dict[str, Any]:
    """Resolve owner/repo from deployment registry, chat text, and GitHub inventory."""
    target = resolve_deployment_target(
        user_text,
        session_id=session_id,
        workspace_hint=workspace_hint,
        user_id=user_id,
        channel=channel,
    )
    if not target.get("ok"):
        return {
            "ok": False,
            "blocker_code": str(target.get("blocker_code") or "REMOTE_REPO_MISSING"),
            "detail": str(target.get("detail") or "Could not determine GitHub repository from the request."),
            "safe_next_command": str(
                target.get("safe_next_command")
                or 'Example: "deploy acme/widget from acme/widget to Vercel"'
            ),
            "deployment_target": target,
        }

    repo = str(target.get("repo") or "")
    branch = str(target.get("branch") or "main")
    github_meta = _lookup_github_repo(repo)
    if not github_meta.get("ok"):
        return {
            "ok": False,
            "blocker_code": "REMOTE_REPO_NOT_FOUND",
            "detail": str(github_meta.get("detail") or f"GitHub repo `{repo}` not accessible."),
            "safe_next_command": "Verify the repo exists and GitHub credentials can read it.",
            "deployment_target": target,
        }

    branch = str(github_meta.get("default_branch") or branch or "main")
    project_name = infer_project_name_from_text(user_text, repo=repo, deployment_target=target)
    owner, name = repo.split("/", 1)

    return {
        "ok": True,
        "blocker_code": "",
        "provider": "github",
        "owner": owner,
        "repo": name,
        "repository": repo,
        "branch": branch,
        "remote_url": str(github_meta.get("html_url") or f"https://github.com/{repo}"),
        "remote_name": "origin",
        "github_repo_id": github_meta.get("repo_id"),
        "project_name": project_name,
        "private": bool(github_meta.get("private")),
        "deployment_target": target,
        "resolution_source": str(target.get("source") or ""),
    }


def format_remote_repo_source_report(source: dict[str, Any]) -> str:
    if not source.get("ok"):
        return (
            f"**Remote repository unavailable** (`{source.get('blocker_code')}`)\n\n"
            f"- Detail: {source.get('detail')}\n\n"
            f"**Required action:** {source.get('safe_next_command')}"
        )
    lines = [
        "**Remote GitHub source**",
        "",
        f"- Repository: `{source.get('repository')}` @ `{source.get('branch')}`",
        f"- Project name: `{source.get('project_name')}`",
        f"- URL: {source.get('remote_url')}",
    ]
    if source.get("resolution_source"):
        lines.append(f"- Resolution: `{source.get('resolution_source')}`")
    target = source.get("deployment_target")
    if isinstance(target, dict) and target.get("alias"):
        lines.append(f"- Target alias: `{target.get('alias')}`")
    return "\n".join(lines)


def _lookup_github_repo(repo: str) -> dict[str, Any]:
    try:
        from aethos_core.credentials import get_provider_api_token
        from aethos_core.providers.github.api_client import find_repository_by_name, parse_owner_repo, request_github

        token = get_provider_api_token("github")
        if not token:
            return {"ok": False, "detail": "GitHub credentials unavailable."}

        found = find_repository_by_name(token, repo)
        if found:
            return {
                "ok": True,
                "repo_id": found.get("repo_id"),
                "default_branch": found.get("default_branch") or "main",
                "html_url": found.get("html_url"),
                "private": found.get("private"),
            }

        owner, name = parse_owner_repo(repo)
        if owner and name:
            resp = request_github(token, "GET", f"/repos/{owner}/{name}")
            if resp.get("ok") and isinstance(resp.get("data"), dict):
                data = resp["data"]
                return {
                    "ok": True,
                    "repo_id": data.get("id"),
                    "default_branch": data.get("default_branch") or "main",
                    "html_url": data.get("html_url"),
                    "private": data.get("private"),
                }
            return {"ok": False, "detail": str(resp.get("error") or "GitHub repo lookup failed.")}
        return {"ok": False, "detail": f"Could not resolve `{repo}`."}
    except Exception as exc:
        return {"ok": False, "detail": str(exc)}
