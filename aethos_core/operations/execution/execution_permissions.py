# SPDX-License-Identifier: Apache-2.0
"""Read-only execution capability matrix — Phase 9.3."""

from __future__ import annotations

from typing import Any

READONLY_ACTIONS = frozenset(
    {
        "git_status",
        "git_branch",
        "git_remote",
        "git_log",
        "git_diff_stat",
        "package_scripts",
        "npm_test",
        "npm_typecheck",
        "url_reachability",
        "vercel_deployment_inspect",
        "vercel_logs_inspect",
        "vercel_api_deployments",
        "vercel_api_domains",
        "vercel_api_project_details",
        "railway_api_deployments",
        "railway_api_project_details",
        "railway_api_logs",
        "github_api_workflow_runs",
        "github_api_workflow_diagnostic",
        "github_api_workflow_jobs",
    }
)

MUTATING_OPERATIONS = frozenset(
    {
        "redeploy",
        "restart",
        "stop",
        "set_env_var",
        "deploy_from_git",
        "local_commit_preflight",
        "local_push_preflight",
        "git_deploy_preflight",
        "workflow_rerun",
        "create_branch",
        "create_pr",
    }
)

CAPABILITY: dict[str, dict[str, Any]] = {
    "git_status": {"read_only": True, "mutating": False, "requires_approval": True},
    "git_branch": {"read_only": True, "mutating": False, "requires_approval": True},
    "git_remote": {"read_only": True, "mutating": False, "requires_approval": True},
    "git_log": {"read_only": True, "mutating": False, "requires_approval": True},
    "package_scripts": {"read_only": True, "mutating": False, "requires_approval": True},
    "npm_test": {"read_only": True, "mutating": False, "requires_approval": True},
    "npm_typecheck": {"read_only": True, "mutating": False, "requires_approval": True},
    "url_reachability": {"read_only": True, "mutating": False, "requires_approval": True},
    "vercel_deployment_inspect": {"read_only": True, "mutating": False, "requires_approval": True},
    "vercel_logs_inspect": {"read_only": True, "mutating": False, "requires_approval": True},
    "vercel_api_deployments": {"read_only": True, "mutating": False, "requires_approval": True},
    "vercel_api_domains": {"read_only": True, "mutating": False, "requires_approval": True},
    "railway_api_deployments": {"read_only": True, "mutating": False, "requires_approval": True},
    "railway_api_project_details": {"read_only": True, "mutating": False, "requires_approval": True},
    "railway_api_logs": {"read_only": True, "mutating": False, "requires_approval": True},
    "github_api_workflow_runs": {"read_only": True, "mutating": False, "requires_approval": True},
    "github_api_workflow_diagnostic": {"read_only": True, "mutating": False, "requires_approval": True},
    "github_api_workflow_jobs": {"read_only": True, "mutating": False, "requires_approval": True},
}


def is_mutating_operation(operation_type: str) -> bool:
    return operation_type in MUTATING_OPERATIONS


def actions_for_operation(operation_type: str, *, provider: str) -> list[str]:
    if is_mutating_operation(operation_type):
        return []
    if provider == "local" or operation_type.startswith("local_"):
        return [
            "git_status",
            "git_branch",
            "git_remote",
            "git_log",
            "package_scripts",
            "npm_typecheck",
            "npm_test",
        ]
    if provider == "railway":
        if operation_type == "list_deployments":
            return ["railway_api_deployments"]
        if operation_type == "project_details":
            return ["railway_api_project_details"]
        if operation_type in ("check_logs", "why_down", "inspect_failed_deployment"):
            return ["railway_api_deployments", "railway_api_logs"]
        return []
    if provider == "github":
        if operation_type == "workflow_runs":
            return ["github_api_workflow_runs"]
        if operation_type == "workflow_diagnostic":
            return ["github_api_workflow_diagnostic"]
        if operation_type == "workflow_jobs":
            return ["github_api_workflow_jobs"]
        return []
    if operation_type == "list_deployments":
        return ["vercel_api_deployments", "url_reachability"]
    if operation_type == "list_domains":
        return ["vercel_api_domains"]
    if operation_type == "project_details":
        return ["vercel_api_project_details"]
    if operation_type in ("check_logs", "why_down", "inspect_failed_deployment"):
        return ["vercel_api_deployments", "url_reachability", "vercel_logs_inspect"]
    if provider == "vercel":
        return ["url_reachability", "vercel_deployment_inspect"]
    return []


def assert_readonly_action(action: str) -> None:
    if action not in READONLY_ACTIONS:
        raise PermissionError(f"Action not allowed for read-only execution: {action}")
