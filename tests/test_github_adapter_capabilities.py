# SPDX-License-Identifier: Apache-2.0
"""GitHub adapter expansion capability tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

import aethos_core.providers  # noqa: F401 — register providers

from aethos_core.capability_truth.provider_capability_matrix import get_provider_summary
from aethos_core.providers.github.expansion.capability_registry import (
    GITHUB_EXPANSION_OPERATIONS,
    github_expansion_summary,
    github_operation_spec,
)
from aethos_core.providers.github.operations.readonly_execution import GitHubReadonlyExecutionAdapter


def test_github_matrix_tier_is_expanding() -> None:
    summary = get_provider_summary("github")
    assert summary is not None
    assert summary.tier == "expanding"
    assert summary.label == "GitHub"
    assert "workflow_rerun" in summary.mutation_ops[0]


def test_github_expansion_registry_marks_push_mutations_expanding() -> None:
    for operation in ("create_branch", "commit_changes", "push_branch", "open_pr"):
        spec = github_operation_spec(operation)
        assert spec is not None
        assert spec.status == "expanding"
        assert spec.enabled is False

    rerun = github_operation_spec("workflow_rerun")
    assert rerun is not None
    assert rerun.status == "wired"
    assert rerun.enabled is True


def test_github_readonly_repo_operations_wired() -> None:
    adapter = GitHubReadonlyExecutionAdapter("test-token")
    repo_payload = {
        "ok": True,
        "repository": "org/app",
        "default_branch": "main",
        "private": False,
        "html_url": "https://github.com/org/app",
        "description": "demo",
        "pushed_at": "2026-05-20T00:00:00Z",
        "repo": {},
    }
    branch_payload = {
        "ok": True,
        "repository": "org/app",
        "branch": "main",
        "protected": False,
        "sha": "abc123",
        "committed_at": "2026-05-20T00:00:00Z",
    }
    commits_payload = {
        "ok": True,
        "repository": "org/app",
        "commits": [{"sha": "abc123", "message": "fix", "author": "dev", "date": "2026-05-20T00:00:00Z"}],
    }
    with patch(
        "aethos_core.providers.github.operations.repo_readonly_api.inspect_repo",
        return_value=repo_payload,
    ), patch(
        "aethos_core.providers.github.operations.repo_readonly_api.fetch_branch_status",
        return_value=branch_payload,
    ), patch(
        "aethos_core.providers.github.operations.repo_readonly_api.fetch_recent_commits",
        return_value=commits_payload,
    ):
        assert adapter.inspect_repo(repository="org/app")["ok"] is True
        assert adapter.get_branch_status(repository="org/app")["branch"] == "main"
        assert len(adapter.get_recent_commits(repository="org/app")["commits"]) == 1


def test_github_expansion_summary_lists_wired_readonly_ops() -> None:
    summary = github_expansion_summary()
    assert "inspect_repo" in summary["readonly_wired"]
    assert "workflow_rerun" in summary["mutations_wired"]
    assert "push_branch" in summary["expanding"]


def test_github_provider_capabilities_include_new_readonly_ops() -> None:
    from aethos_core.providers.github.provider import GITHUB_CAPABILITIES

    for operation in ("inspect_repo", "branch_status", "recent_commits", "failed_checks"):
        assert GITHUB_CAPABILITIES[operation]["enabled"] is True

    assert GITHUB_CAPABILITIES["push_branch"]["enabled"] is False
