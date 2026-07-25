# SPDX-License-Identifier: Apache-2.0
"""GitHub adapter expansion registry — honest wired vs expanding operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

OperationStatus = Literal["wired", "expanding", "planned"]
OperationCategory = Literal["readonly", "mutation", "verification"]


@dataclass(frozen=True)
class GitHubOperationSpec:
    operation: str
    category: OperationCategory
    status: OperationStatus
    enabled: bool
    summary: str


GITHUB_EXPANSION_OPERATIONS: tuple[GitHubOperationSpec, ...] = (
    GitHubOperationSpec("inspect_repo", "readonly", "wired", True, "Repository metadata via GitHub API"),
    GitHubOperationSpec("branch_status", "readonly", "wired", True, "Default branch and branch head status"),
    GitHubOperationSpec("recent_commits", "readonly", "wired", True, "Recent commit history"),
    GitHubOperationSpec("workflow_runs", "readonly", "wired", True, "Workflow run listing"),
    GitHubOperationSpec("workflow_diagnostic", "readonly", "wired", True, "Failed workflow diagnostics"),
    GitHubOperationSpec("workflow_jobs", "readonly", "wired", True, "Failed job/step evidence"),
    GitHubOperationSpec("failed_checks", "readonly", "wired", True, "Check run / PR check failures"),
    GitHubOperationSpec("branch_divergence", "readonly", "wired", True, "Branch ahead/behind compare evidence"),
    GitHubOperationSpec("pr_status", "readonly", "wired", True, "Open pull request status"),
    GitHubOperationSpec("releases", "readonly", "wired", True, "Release and tag inspection"),
    GitHubOperationSpec("live_diagnosis", "readonly", "wired", True, "Multi-source GitHub live readonly diagnostics"),
    GitHubOperationSpec("deploy_correlation", "readonly", "wired", True, "Correlate GitHub CI failures with deploy providers"),
    GitHubOperationSpec("workflow_logs", "readonly", "expanding", True, "Workflow job log metadata (full log streaming expanding)"),
    GitHubOperationSpec("workflow_rerun", "mutation", "wired", True, "Governed workflow rerun"),
    GitHubOperationSpec("create_branch", "mutation", "expanding", False, "Governed branch creation — approval gated, wiring in progress"),
    GitHubOperationSpec("commit_changes", "mutation", "expanding", False, "Governed local commit push path — wiring in progress"),
    GitHubOperationSpec("push_branch", "mutation", "expanding", False, "Governed branch push — wiring in progress"),
    GitHubOperationSpec("open_pr", "mutation", "expanding", False, "Governed pull request creation — wiring in progress"),
    GitHubOperationSpec("cancel_workflow", "mutation", "expanding", False, "Governed workflow cancel — wiring in progress"),
    GitHubOperationSpec("workflow_status", "verification", "wired", True, "Post-mutation workflow status checks"),
    GitHubOperationSpec("pr_checks", "verification", "expanding", False, "PR check verification — wiring in progress"),
    GitHubOperationSpec("failure_summary", "verification", "wired", True, "Summarize workflow/check failures"),
    GitHubOperationSpec("outcome_learning", "verification", "expanding", False, "Repair outcome learning for GitHub mutations"),
)


def github_operation_spec(operation: str) -> GitHubOperationSpec | None:
    key = (operation or "").strip().lower()
    for spec in GITHUB_EXPANSION_OPERATIONS:
        if spec.operation == key:
            return spec
    return None


def github_operations_by_status(status: OperationStatus) -> list[GitHubOperationSpec]:
    return [spec for spec in GITHUB_EXPANSION_OPERATIONS if spec.status == status]


def github_expansion_summary() -> dict[str, list[str]]:
    readonly = [spec.operation for spec in GITHUB_EXPANSION_OPERATIONS if spec.category == "readonly" and spec.enabled]
    mutations = [spec.operation for spec in GITHUB_EXPANSION_OPERATIONS if spec.category == "mutation" and spec.enabled]
    expanding = [spec.operation for spec in GITHUB_EXPANSION_OPERATIONS if spec.status == "expanding"]
    planned = [spec.operation for spec in GITHUB_EXPANSION_OPERATIONS if spec.status == "planned"]
    return {
        "readonly_wired": readonly,
        "mutations_wired": [spec.operation for spec in GITHUB_EXPANSION_OPERATIONS if spec.category == "mutation" and spec.status == "wired"],
        "expanding": expanding,
        "planned": planned,
    }
