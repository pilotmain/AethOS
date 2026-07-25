# SPDX-License-Identifier: Apache-2.0
"""GitHub live readonly diagnostics tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.provider_readonly_intent.readonly_intent_classifier import classify_github_readonly_intent
from aethos_core.provider_readonly_intent.readonly_provider_router import route_readonly_provider_question
from aethos_core.providers.github.diagnostics.diagnosis_composer import compose_github_live_diagnosis_reply
from aethos_core.providers.github.diagnostics.github_live_diagnostics import run_github_live_diagnostics


@pytest.fixture
def sample_evidence() -> dict:
    return {
        "ok": True,
        "repository": "pilotmain/aethos",
        "operation": "live_diagnosis",
        "repo": {
            "ok": True,
            "repository": "pilotmain/aethos",
            "default_branch": "main",
            "private": False,
            "pushed_at": "2026-05-20T00:00:00Z",
        },
        "branch": {
            "ok": True,
            "branch": "main",
            "sha": "abc123def4567890",
            "protected": True,
        },
        "divergence": {
            "ok": True,
            "base": "main",
            "head": "main",
            "ahead_by": 0,
            "behind_by": 2,
            "status": "behind",
        },
        "local_changes_note": "Remote divergence detected (2 commit(s) behind).",
        "commits": {
            "ok": True,
            "commits": [{"sha": "abc123", "message": "fix deploy", "author": "raya"}],
        },
        "checks": {
            "ok": True,
            "failed_count": 1,
            "checks": [{"name": "ci/build", "conclusion": "failure"}],
        },
        "workflow_runs": {
            "ok": True,
            "runs": [
                {
                    "name": "Deploy",
                    "conclusion": "failure",
                    "head_branch": "main",
                    "run_number": 42,
                }
            ],
        },
        "workflow_diagnostic": {
            "ok": True,
            "latest_failed_run": {
                "name": "Deploy",
                "run_number": 42,
                "head_branch": "main",
                "conclusion": "failure",
            },
            "likely_failure_job": "build",
            "likely_failure_step": "Run tests",
        },
        "workflow_jobs": {"ok": True, "failed_jobs": [{"name": "build"}]},
        "pull_requests": {
            "ok": True,
            "pull_requests": [
                {
                    "number": 7,
                    "title": "Fix deploy",
                    "head": "fix/deploy",
                    "base": "main",
                    "mergeable_state": "blocked",
                }
            ],
        },
        "releases": {
            "ok": True,
            "latest_release": {"name": "v1.2.0", "tag_name": "v1.2.0"},
            "latest_tag": "v1.2.0",
        },
        "deploy_correlation": {
            "lines": [
                "GitHub Actions failure `Deploy` on branch `main` may block downstream deploy.",
                "Latest failed workflow: **Deploy** run #42 on `main`.",
            ],
            "deploy_related_failures": 1,
        },
    }


def test_classifier_maps_new_github_readonly_operations() -> None:
    assert classify_github_readonly_intent("diagnose github repo pilotmain/aethos").operation == "live_diagnosis"
    assert classify_github_readonly_intent("inspect github branch divergence for pilotmain/aethos").operation == "branch_divergence"
    assert classify_github_readonly_intent("check github pull request status for pilotmain/aethos").operation == "pr_status"
    assert classify_github_readonly_intent("inspect github releases for pilotmain/aethos").operation == "releases"
    assert classify_github_readonly_intent("why did github workflow fail for pilotmain/aethos").operation == "workflow_failures"


def test_compose_live_diagnosis_includes_operator_sections(sample_evidence: dict) -> None:
    reply = compose_github_live_diagnosis_reply(sample_evidence, operation="live_diagnosis")
    assert "GitHub live diagnostics" in reply
    assert "Branch divergence" in reply
    assert "Workflow failures" in reply
    assert "Failed checks" in reply
    assert "Deploy correlation" in reply
    assert "Next readonly evidence step" in reply
    assert "workflow rerun only" in reply
    assert "No mutation has been performed" in reply


def test_compose_workflow_failures_focus(sample_evidence: dict) -> None:
    reply = compose_github_live_diagnosis_reply(sample_evidence, operation="workflow_failures")
    assert "Workflow failures" in reply
    assert "Operator summary" in reply
    assert "build" in reply


@patch("aethos_core.providers.github.diagnostics.github_live_diagnostics.collect_github_live_evidence")
def test_run_github_live_diagnostics_returns_meta(mock_collect, sample_evidence: dict) -> None:
    mock_collect.return_value = sample_evidence
    reply, meta = run_github_live_diagnostics(
        "token",
        repository="pilotmain/aethos",
        session_id="gh-live",
        operation="live_diagnosis",
    )
    assert "GitHub live diagnostics" in reply
    assert meta["github_live_diagnostics"] == "true"
    assert meta["workflow_failures"] == "true"


@patch("aethos_core.providers.github.diagnostics.github_live_diagnostics.collect_github_live_evidence")
def test_route_readonly_github_live_diagnosis(mock_collect, sample_evidence: dict) -> None:
    mock_collect.return_value = sample_evidence
    with patch(
        "aethos_core.runtime.github_readonly_jobs.resolve_github_auth_for_chat",
        return_value={"auth_method": "api_token", "credential_id": "gh-cred", "block_reason": None},
    ), patch(
        "aethos_core.providers.github.auth.GitHubAuthAdapter.get_api_token",
        return_value="test-token",
    ):
        result = route_readonly_provider_question(
            "diagnose github repo pilotmain/aethos workflow failures",
            session_id="gh-live-route",
        )
    assert result is not None
    assert result.meta.get("readonly_operation") in {"live_diagnosis", "workflow_failures"}
    assert "Deploy correlation" in result.reply
    assert "workflow rerun only" in result.reply
