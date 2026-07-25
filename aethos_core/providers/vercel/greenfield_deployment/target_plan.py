# SPDX-License-Identifier: Apache-2.0
"""Vercel greenfield target plan from local workspace."""

from __future__ import annotations

from typing import Any


def build_vercel_greenfield_target_plan(
    *,
    repo_full_name: str,
    branch: str,
    project_name: str,
    framework: str = "other",
    root_directory: str = "",
    deployment_target: dict[str, Any] | None = None,
) -> dict[str, Any]:
    target = deployment_target if isinstance(deployment_target, dict) else {}
    resolved_root = str(target.get("root_directory") or root_directory or "")
    resolved_project = str(target.get("vercel_project") or project_name)
    return {
        "provider": "vercel",
        "project": resolved_project,
        "project_name": resolved_project,
        "repo": repo_full_name,
        "branch": branch,
        "framework": framework,
        "root_directory": resolved_root,
        "risk_tier": "staging",
        "deployment_target_id": str(target.get("target_id") or ""),
        "deployment_target_alias": str(target.get("alias") or ""),
    }


def format_vercel_greenfield_target_plan(plan: dict[str, Any]) -> str:
    lines = [
        f"Project: `{plan.get('project_name')}`",
        f"Repository: `{plan.get('repo')}` @ `{plan.get('branch')}`",
        f"Framework hint: `{plan.get('framework')}`",
    ]
    if plan.get("root_directory"):
        lines.append(f"Root directory: `{plan.get('root_directory')}`")
    return "\n".join(lines)
