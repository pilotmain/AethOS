# SPDX-License-Identifier: Apache-2.0
"""Phase 3 — Railway greenfield target plan (no mutations)."""

from __future__ import annotations

from typing import Any

from aethos_core.config import get_settings
from aethos_core.providers.railway.deployment_plan.deployment_plan_artifact import (
    classify_plan_risk,
    parse_plan_fields_from_text,
)


def build_railway_greenfield_target_plan(
    *,
    user_text: str,
    git_remote: dict[str, Any],
    local_source: dict[str, Any],
    local_inspection: dict[str, Any],
    deployment_target: dict[str, Any] | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    parsed = parse_plan_fields_from_text(user_text, default_repo=str(git_remote.get("repository") or ""))
    from aethos_core.providers.railway.greenfield_deployment.git_remote_resolution import (
        normalize_github_repository_slug,
    )
    from aethos_core.providers.railway.greenfield_deployment.greenfield_deploy_component import (
        detect_greenfield_deploy_component,
        greenfield_root_directory,
        infer_greenfield_service_name,
    )

    repo = normalize_github_repository_slug(str(parsed.get("repo") or git_remote.get("repository") or ""))
    branch = str(parsed.get("branch") or git_remote.get("branch") or "main")
    component = detect_greenfield_deploy_component(user_text)
    service_name = str(
        parsed.get("service_name")
        or infer_greenfield_service_name(text=user_text, repo=repo, component=component)
    )
    project = str(parsed.get("project") or "").strip() or _default_project(settings)
    environment = str(parsed.get("environment") or "").strip() or _default_environment(settings)
    root_directory = greenfield_root_directory(component=component)

    target = deployment_target if isinstance(deployment_target, dict) else {}
    if target.get("railway_project"):
        project = str(target["railway_project"])
    if target.get("railway_service"):
        service_name = str(target["railway_service"])
    if target.get("railway_environment"):
        environment = str(target["railway_environment"])
    if target.get("root_directory"):
        root_directory = str(target["root_directory"])

    return {
        "ok": bool(repo),
        "flow": "railway_greenfield_deployment",
        "deploy_component": component,
        "root_directory": root_directory,
        "repo": repo,
        "branch": branch,
        "project": project,
        "environment": environment,
        "service_name": service_name,
        "runtime": str(local_inspection.get("runtime") or "unknown"),
        "build_command": str(local_inspection.get("build_command") or "unknown"),
        "start_command": str(local_inspection.get("start_command") or "unknown"),
        "health_check_path": str(local_inspection.get("health_check_path") or "unknown"),
        "workspace_root": str(local_source.get("workspace_root") or ""),
        "workspace_name": str(local_source.get("workspace_name") or ""),
        "remote_url": str(git_remote.get("remote_url") or ""),
        "risk_tier": classify_plan_risk(environment=environment).value,
        "required_env_var_names": list(local_inspection.get("required_env_var_names") or []),
        "mutation_performed": False,
    }


def format_railway_greenfield_target_plan(plan: dict[str, Any]) -> str:
    component = str(plan.get("deploy_component") or "api")
    root = str(plan.get("root_directory") or "")
    lines = [
        "**Railway greenfield target plan** (draft — no mutation)",
        "",
        f"- Component: `{component}`",
        f"- New project: `{plan.get('project')}`",
        f"- New service: `{plan.get('service_name')}`",
        f"- Environment: `{plan.get('environment')}`",
        f"- Source: `{plan.get('repo')}` @ `{plan.get('branch')}`",
    ]
    if root:
        lines.append(f"- Root directory: `{root}`")
    lines.extend(
        [
            f"- Runtime: {plan.get('runtime')}",
            f"- Build: `{plan.get('build_command')}`",
            f"- Start: `{plan.get('start_command')}`",
            f"- Risk: `{plan.get('risk_tier')}`",
        ]
    )
    return "\n".join(lines)


def _default_project(settings: Any) -> str:
    allowed = str(getattr(settings, "railway_greenfield_allowed_projects", "pilotos") or "pilotos")
    first = allowed.split(",")[0].strip()
    return first or "pilotos"


def _default_environment(settings: Any) -> str:
    allowed = str(getattr(settings, "railway_greenfield_allowed_environments", "staging") or "staging")
    first = allowed.split(",")[0].strip()
    return first or "staging"
