# SPDX-License-Identifier: Apache-2.0
"""Readonly local repo inspection for greenfield env/build detection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aethos_core.providers.railway.deployment_plan.repo_inspection import (
    extract_env_var_hints_from_text,
    extract_env_var_names_from_text,
)
from aethos_core.providers.railway.env_value_readiness.env_deployment_filter import (
    filter_greenfield_deployment_env_var_names,
)


def inspect_local_repo_for_deployment(workspace_root: str | Path) -> dict[str, Any]:
    root = Path(workspace_root)
    if not root.is_dir():
        return {"ok": False, "error": "workspace not found", "required_env_var_names": []}

    file_contents: dict[str, str] = {}
    for rel in (
        ".env.example",
        "package.json",
        "web/package.json",
        "pyproject.toml",
        "Dockerfile",
        "Procfile",
        "railway.json",
        "README.md",
    ):
        path = root / rel
        if path.is_file():
            try:
                file_contents[rel] = path.read_text(encoding="utf-8", errors="replace")[:24000]
            except OSError:
                continue

    env_names: list[str] = []
    env_var_hints: dict[str, str] = {}
    if ".env.example" in file_contents:
        env_names.extend(extract_env_var_names_from_text(file_contents[".env.example"]))
        env_var_hints = extract_env_var_hints_from_text(file_contents[".env.example"])
    env_names = sorted({n for n in env_names if n and not n.startswith("#")})

    runtime = "unknown"
    build_command = "unknown"
    start_command = "unknown"
    health_check_path = "unknown"

    if "Dockerfile" in file_contents:
        runtime = "Docker"
        build_command = "docker build ."
    if "package.json" in file_contents or "web/package.json" in file_contents:
        runtime = "Node" if runtime == "unknown" else runtime
        pkg_path = "web/package.json" if "web/package.json" in file_contents else "package.json"
        try:
            pkg = json.loads(file_contents[pkg_path])
            scripts = dict(pkg.get("scripts") or {})
            if scripts.get("build"):
                build_command = "npm run build"
            if scripts.get("start"):
                start_command = "npm start"
        except json.JSONDecodeError:
            pass
    if "pyproject.toml" in file_contents or (root / "requirements.txt").is_file():
        runtime = "Python" if runtime == "unknown" else runtime
        if build_command == "unknown":
            build_command = "pip install -r requirements.txt" if (root / "requirements.txt").is_file() else "pip install ."
        if start_command == "unknown":
            start_command = "uvicorn aethos_core.api.main:app --host 0.0.0.0 --port ${PORT:-8010}"

    return {
        "ok": True,
        "files_inspected": sorted(file_contents.keys()),
        "runtime": runtime,
        "build_command": build_command,
        "start_command": start_command,
        "health_check_path": health_check_path,
        "required_env_var_names": env_names,
        "env_var_hints": env_var_hints,
    }


def build_required_env_var_report(
    inspection: dict[str, Any],
    *,
    git_remote: dict[str, Any],
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    plan_payload = dict(plan or {})
    if git_remote.get("repository") and not plan_payload.get("repo"):
        plan_payload["repo"] = git_remote.get("repository")
    if git_remote.get("branch") and not plan_payload.get("branch"):
        plan_payload["branch"] = git_remote.get("branch")

    all_names = list(inspection.get("required_env_var_names") or [])
    names = filter_greenfield_deployment_env_var_names(all_names, plan=plan_payload)
    secure_refs = [f"secure_store://env/{name}" for name in names]
    return {
        "ok": True,
        "required_env_var_names": names,
        "all_detected_env_var_names": all_names,
        "secure_references": secure_refs,
        "names_only": True,
        "repository": git_remote.get("repository"),
        "branch": git_remote.get("branch"),
        "count": len(names),
        "env_var_hints": dict(inspection.get("env_var_hints") or plan_payload.get("env_var_hints") or {}),
    }


def format_required_env_var_report(report: dict[str, Any]) -> str:
    names = list(report.get("required_env_var_names") or [])
    lines = [
        "**Required environment variables (names only)**",
        "",
        f"- Count: **{len(names)}**",
    ]
    if names:
        preview = ", ".join(f"`{n}`" for n in names[:12])
        suffix = f" (+{len(names) - 12} more)" if len(names) > 12 else ""
        lines.append(f"- Names: {preview}{suffix}")
        lines.append("- Values: loaded from secure store at execution time — never pasted in chat.")
    else:
        lines.append("- No names detected from `.env.example` — runtime schema defaults may still apply.")
    return "\n".join(lines)
