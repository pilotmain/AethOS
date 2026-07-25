# SPDX-License-Identifier: Apache-2.0
"""GitHub issue intake — governed self-improvement (Phase 9.7)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class IssueIntakePlan:
    repository: str
    issue_number: int | None
    title: str
    summary: str
    execution_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "issue_number": self.issue_number,
            "title": self.title,
            "summary": self.summary,
            "execution_enabled": self.execution_enabled,
            "phase": "9.7",
        }


def fetch_github_issues(*, repository: str, limit: int = 10) -> dict[str, Any]:
    from aethos_core.providers.github.auth import GitHubAuthAdapter
    from aethos_core.providers.github.operations.repo_readonly_api import list_open_issues

    auth = GitHubAuthAdapter().resolve_best_auth_method(operation="read_repos")
    credential_id = auth.get("credential_id")
    if not credential_id:
        return {"ok": False, "error": "GitHub credential unavailable.", "issues": []}
    token = GitHubAuthAdapter().get_api_token(str(credential_id))
    if not token:
        return {"ok": False, "error": "GitHub token unavailable.", "issues": []}
    return list_open_issues(token, repository=repository, limit=limit)


def plan_from_issue_prompt(*, repository: str, issue_hint: str | None = None) -> IssueIntakePlan:
    return IssueIntakePlan(
        repository=repository,
        issue_number=int(issue_hint) if issue_hint and issue_hint.isdigit() else None,
        title=f"Self-improvement plan for {repository}",
        summary=(
            "Analyze issue · plan bounded changes · create branch · generate PR · run tests · "
            "human review required — no automatic merge."
        ),
    )
