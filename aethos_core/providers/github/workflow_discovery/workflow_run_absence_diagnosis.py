# SPDX-License-Identifier: Apache-2.0
"""Diagnose why no GitHub workflow runs exist for rerun."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.github.operations.repo_readonly_api import fetch_branch_status, fetch_recent_commits
from aethos_core.providers.github.shared.auth_diagnostics import github_discovery_auth_diagnostics
from aethos_core.providers.github.workflow_discovery.actions_enablement_checker import check_actions_enablement
from aethos_core.providers.github.workflow_discovery.workflow_file_discovery import discover_workflow_files
from aethos_core.providers.github.workflow_discovery.workflow_trigger_analyzer import analyze_workflow_files


def diagnose_workflow_run_absence(
    token: str,
    *,
    repository: str,
    branch: str | None = None,
) -> dict[str, Any]:
    files = discover_workflow_files(token, repository=repository, ref=branch)
    repo = str(files.get("repository") or repository)
    default_branch = str(files.get("default_branch") or branch or "main")
    active_branch = str(files.get("ref") or default_branch)

    enablement = check_actions_enablement(token, repository=repo)
    trigger_analysis = analyze_workflow_files(list(files.get("workflow_files") or []))
    auth = github_discovery_auth_diagnostics(token, repository=repo)
    branch_status = fetch_branch_status(token, repository=repo, branch=active_branch)
    commits = fetch_recent_commits(token, repository=repo, limit=5)
    workflow_touch = _recent_workflow_commit_touch(list(commits.get("commits") or []))

    likely_reason = _infer_likely_reason(
        files=files,
        enablement=enablement,
        trigger_analysis=trigger_analysis,
        auth=auth,
    )
    next_steps = _next_steps(
        files=files,
        enablement=enablement,
        trigger_analysis=trigger_analysis,
        auth=auth,
    )

    return {
        "ok": bool(files.get("ok")),
        "repository": repo,
        "default_branch": default_branch,
        "active_branch": active_branch,
        "workflows_dir_found": bool(files.get("workflows_dir_found")),
        "workflow_file_names": list(files.get("workflow_file_names") or []),
        "workflow_files": list(files.get("workflow_files") or []),
        "trigger_analysis": trigger_analysis,
        "actions_status": enablement.get("actions_status"),
        "actions_enabled": enablement.get("actions_enabled"),
        "registered_workflow_count": enablement.get("registered_workflow_count"),
        "disabled_workflow_count": enablement.get("disabled_workflow_count"),
        "permissions_readable": enablement.get("permissions_readable"),
        "workflows_api_readable": enablement.get("workflows_api_readable"),
        "auth_state": auth.get("auth_state"),
        "workflow_scope_present": auth.get("workflow_scope_present"),
        "branch_status": branch_status,
        "recent_commits": list(commits.get("commits") or []),
        "recent_workflow_commit_touch": workflow_touch,
        "likely_reason": likely_reason,
        "next_steps": next_steps,
        "errors": _collect_errors(files, enablement, auth, branch_status, commits),
    }


def _infer_likely_reason(
    *,
    files: dict[str, Any],
    enablement: dict[str, Any],
    trigger_analysis: dict[str, Any],
    auth: dict[str, Any],
) -> str:
    if str(auth.get("auth_state") or "") in {"missing", "invalid", "insufficient_scope"}:
        return "GitHub token auth or Actions read scope may be preventing workflow run discovery."
    if not files.get("workflows_dir_found"):
        return "No `.github/workflows/` directory exists on the inspected branch — GitHub Actions workflows are not configured."
    if enablement.get("actions_status") == "disabled":
        return "GitHub Actions appears disabled for this repository."
    if enablement.get("actions_status") == "unknown_permission":
        return "Workflow files may exist, but Actions permissions could not be verified with the current token."
    if not trigger_analysis.get("workflow_count"):
        return "The workflows directory exists but no workflow YAML files were found."
    if trigger_analysis.get("parse_failures"):
        return "Workflow YAML files exist but at least one file could not be parsed for triggers."
    if enablement.get("disabled_workflow_count") and enablement.get("registered_workflow_count"):
        if enablement.get("disabled_workflow_count") == enablement.get("registered_workflow_count"):
            return "Registered GitHub Actions workflows are disabled."
    if trigger_analysis.get("has_workflow_dispatch") and not (
        trigger_analysis.get("has_push_trigger") or trigger_analysis.get("has_pull_request_trigger")
    ):
        return "Workflows exist but only manual `workflow_dispatch` triggers were detected — no run has been dispatched yet."
    if trigger_analysis.get("all_triggers") and not trigger_analysis.get("has_push_trigger"):
        return "Workflows exist but may not run automatically on push to the default branch — no workflow run history yet."
    if files.get("workflows_dir_found") and trigger_analysis.get("workflow_count"):
        return "Workflow files exist, but GitHub has no recorded workflow runs yet for this repository."
    return "No workflow run history is available to rerun."


def _next_steps(
    *,
    files: dict[str, Any],
    enablement: dict[str, Any],
    trigger_analysis: dict[str, Any],
    auth: dict[str, Any],
) -> list[str]:
    steps: list[str] = []
    if str(auth.get("auth_state") or "") in {"missing", "invalid", "insufficient_scope"}:
        steps.append("Configure a GitHub token with repo and Actions read access, then rerun readonly diagnostics.")
    if not files.get("workflows_dir_found"):
        steps.extend(
            [
                "Add a workflow under `.github/workflows/` (for example `ci.yml`).",
                "Push a commit to the default branch to trigger the workflow.",
            ]
        )
        return steps
    if enablement.get("actions_status") == "disabled":
        steps.append("Enable GitHub Actions for the repository in GitHub settings.")
    if trigger_analysis.get("has_workflow_dispatch"):
        steps.append("Manually dispatch the workflow from GitHub Actions if `workflow_dispatch` is configured.")
    if trigger_analysis.get("has_push_trigger") or trigger_analysis.get("has_pull_request_trigger"):
        steps.append("Push a commit or open a pull request that matches the workflow trigger.")
    if not steps:
        steps.extend(
            [
                "Inspect recent workflow runs in GitHub Actions UI.",
                "Verify the default branch and workflow triggers match your expected CI path.",
            ]
        )
    return steps


def _recent_workflow_commit_touch(commits: list[dict[str, Any]]) -> bool:
    for row in commits:
        message = str(row.get("message") or "").lower()
        if "workflow" in message or ".github" in message:
            return True
    return False


def _collect_errors(*payloads: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for payload in payloads:
        err = str(payload.get("error") or "").strip()
        if err:
            errors.append(err)
    return errors
