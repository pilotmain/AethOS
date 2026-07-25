# SPDX-License-Identifier: Apache-2.0
"""Inspect remote GitHub repos for greenfield Vercel deployment."""

from __future__ import annotations

import base64
import json
from typing import Any

from aethos_core.providers.railway.deployment_plan.repo_inspection import extract_env_var_names_from_text


def inspect_remote_github_repo_for_deployment(
    *,
    repository: str,
    branch: str = "main",
) -> dict[str, Any]:
    """Fetch deployment hints from GitHub — never raises."""
    owner, repo = _split_repo(repository)
    if not owner or not repo:
        return {"ok": False, "error": "invalid repository", "required_env_var_names": []}

    file_contents: dict[str, str] = {}
    for rel in (
        ".env.example",
        ".env.local.example",
        "package.json",
        "web/package.json",
        "pyproject.toml",
        "Dockerfile",
        "vercel.json",
        "README.md",
    ):
        text = _fetch_github_file(owner, repo, rel, ref=branch)
        if text:
            file_contents[rel] = text[:24000]

    env_names: list[str] = []
    for key in (".env.example", ".env.local.example"):
        if key in file_contents:
            env_names.extend(extract_env_var_names_from_text(file_contents[key]))
    env_names = sorted({n for n in env_names if n and not n.startswith("#")})

    runtime = "unknown"
    build_command = "unknown"
    start_command = "unknown"
    framework = "other"

    pkg_path = "web/package.json" if "web/package.json" in file_contents else "package.json"
    if pkg_path in file_contents:
        runtime = "Node"
        framework = "nextjs"
        try:
            pkg = json.loads(file_contents[pkg_path])
            scripts = dict(pkg.get("scripts") or {})
            if scripts.get("build"):
                build_command = "npm run build"
            if scripts.get("start"):
                start_command = "npm start"
            deps = dict(pkg.get("dependencies") or {})
            if "next" in deps:
                framework = "nextjs"
        except json.JSONDecodeError:
            pass
    elif "Dockerfile" in file_contents:
        runtime = "Docker"
        build_command = "docker build ."
    elif "pyproject.toml" in file_contents:
        runtime = "Python"
        build_command = "pip install ."

    return {
        "ok": True,
        "source": "github_remote",
        "repository": f"{owner}/{repo}",
        "branch": branch,
        "files_inspected": sorted(file_contents.keys()),
        "runtime": runtime,
        "framework": framework,
        "build_command": build_command,
        "start_command": start_command,
        "health_check_path": "/",
        "required_env_var_names": env_names,
    }


def _split_repo(repository: str) -> tuple[str, str]:
    raw = (repository or "").strip().strip("/")
    if "/" not in raw:
        return "", raw
    owner, repo = raw.split("/", 1)
    return owner.strip(), repo.strip()


def _fetch_github_file(owner: str, repo: str, path: str, *, ref: str) -> str | None:
    try:
        from aethos_core.credentials import get_provider_api_token
        from aethos_core.providers.github.api_client import request_github

        token = get_provider_api_token("github")
        if not token:
            return None
        resp = request_github(
            token,
            "GET",
            f"/repos/{owner}/{repo}/contents/{path}",
            params={"ref": ref},
        )
        if not resp.get("ok"):
            return None
        data = resp.get("data")
        if not isinstance(data, dict) or not data.get("content"):
            return None
        return base64.b64decode(str(data["content"])).decode("utf-8", errors="replace")
    except Exception:
        return None
