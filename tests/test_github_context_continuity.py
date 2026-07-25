# SPDX-License-Identifier: Apache-2.0
"""GitHub context continuity tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.operations.mutations.preflight import run_mutation_preflight
from aethos_core.providers.github.context.github_context_store import (
    assert_valid_repo_context,
    clear_github_context_for_tests,
    get_active_github_context,
    resolve_rerun_repository,
    save_github_context_from_evidence,
)
from aethos_core.providers.github.mutations.workflow_rerun_preflight import prepare_workflow_rerun_preflight


@pytest.fixture
def mutation_enabled(monkeypatch):
    from aethos_core.config import get_settings

    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("MUTATION_T3_PRODUCTION_ENABLED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def setup_function() -> None:
    clear_github_context_for_tests()


def _diagnostic_evidence(*, failed: bool = True) -> dict:
    latest_failed = (
        {
            "id": 123456,
            "name": "CI",
            "run_number": 42,
            "head_branch": "main",
            "head_sha": "abc123def456",
            "status": "completed",
            "conclusion": "failure",
        }
        if failed
        else None
    )
    return {
        "repository": "pilotmain/aethos",
        "repo": {"full_name": "pilotmain/aethos", "default_branch": "main"},
        "branch": {"branch": "main", "sha": "abc123def456"},
        "commits": {"commits": [{"sha": "abc123def456", "message": "fix", "author": "raya"}]},
        "checks": {"ok": True, "failed_count": 1 if failed else 0, "checks": []},
        "workflow_runs": {
            "ok": True,
            "runs": [
                {
                    "id": 123456,
                    "name": "CI",
                    "conclusion": "failure" if failed else "success",
                    "head_branch": "main",
                    "head_sha": "abc123def456",
                }
            ],
        },
        "workflow_diagnostic": {"ok": True, "latest_failed_run": latest_failed},
    }


def test_diagnose_repo_stores_active_github_context() -> None:
    save_github_context_from_evidence("ctx-session", _diagnostic_evidence())
    ctx = get_active_github_context("ctx-session")
    assert ctx is not None
    assert ctx["repo_full_name"] == "pilotmain/aethos"
    assert ctx["owner"] == "pilotmain"
    assert ctx["repo"] == "aethos"
    assert ctx["latest_failed_run"]["id"] == 123456


def test_rerun_uses_active_context_without_reasking_repo() -> None:
    save_github_context_from_evidence("rerun-session", _diagnostic_evidence())
    resolved = resolve_rerun_repository(
        session_id="rerun-session",
        user_request="rerun the failed GitHub workflow",
    )
    assert resolved["repo"] == "pilotmain/aethos"
    assert resolved["source"] == "github_context"

    result = prepare_workflow_rerun_preflight(
        session_id="rerun-session",
        target_name="",
        user_request="rerun the failed GitHub workflow",
    )
    assert result.get("ok") is True
    assert result.get("repository") == "pilotmain/aethos"
    assert result.get("source_run_id") == 123456


def test_no_failed_workflow_gives_no_rerun_guidance() -> None:
    save_github_context_from_evidence("no-fail-session", _diagnostic_evidence(failed=False))
    with patch(
        "aethos_core.providers.github.mutations.workflow_rerun_preflight.discover_workflow_rerun_from_readonly_substrate",
        return_value={"ok": False, "error": "none"},
    ):
        result = prepare_workflow_rerun_preflight(
            session_id="no-fail-session",
            target_name="",
            user_request="rerun the failed GitHub workflow",
        )
    assert result.get("no_failed_workflow") is True
    text = "\n".join(result.get("preflight_sections") or [])
    assert "pilotmain/aethos" in text
    assert "no failed workflow run is available" in text


@pytest.mark.parametrize(
    "repo",
    ["owner/aethos", "owner/repo", "unknown/aethos"],
)
def test_placeholder_repo_blocked(repo: str) -> None:
    valid, err = assert_valid_repo_context(repo)
    assert valid is False
    assert err is not None


@patch("aethos_core.operations.mutations.preflight._mutation_provider_auth_block", return_value=None)
@patch("aethos_core.providers.github.mutations.workflow_rerun_preflight.prepare_workflow_rerun_preflight")
def test_mutation_preflight_uses_context_when_no_target_name(mock_prepare, _auth, mutation_enabled) -> None:
    mock_prepare.return_value = {
        "ok": True,
        "repository": "pilotmain/aethos",
        "workflow_name": "CI",
        "source_run_id": 123456,
        "head_branch": "main",
        "head_sha": "abc123def456",
        "preflight_sections": ["Created governed GitHub workflow rerun preflight."],
    }
    outcome = run_mutation_preflight(
        job_type="mutation_preflight",
        params={
            "user_request": "rerun the failed GitHub workflow",
            "provider": "github",
            "operation_type": "workflow_rerun",
            "session_id": "ctx-preflight",
        },
    )
    assert outcome.target_name == "pilotmain/aethos"
    assert outcome.preflight_status == "ready_for_mutation_approval"
    mock_prepare.assert_called_once()
    assert mock_prepare.call_args.kwargs["session_id"] == "ctx-preflight"
