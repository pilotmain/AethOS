# SPDX-License-Identifier: Apache-2.0
"""GitHub rerun pending intent continuation tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.provider_readonly_intent.github_readonly_router import compose_github_readonly_route_reply
from aethos_core.provider_readonly_intent.readonly_intent_classifier import classify_github_readonly_intent
from aethos_core.providers.github.context.github_context_store import (
    clear_github_context_for_tests,
    save_github_context_from_evidence,
)
from aethos_core.providers.github.mutations.rerun_intent_continuation import (
    clear_pending_rerun_intent_for_tests,
    compose_github_workflow_rerun_route_reply,
    get_pending_rerun_intent,
    is_pending_rerun_repo_reply,
)


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
    clear_pending_rerun_intent_for_tests()


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
        "workflow_runs": {"ok": True, "runs": []},
        "workflow_diagnostic": {"ok": True, "latest_failed_run": latest_failed},
    }


@patch("aethos_core.chat.mutation_preflight_prompts.create_mutation_preflight_job_reply")
def test_active_context_used_by_rerun_command(mock_preflight, mutation_enabled) -> None:
    save_github_context_from_evidence("ctx-rerun", _diagnostic_evidence())
    mock_preflight.return_value = (
        "Created governed GitHub workflow rerun preflight `job-1`.",
        "mutation_preflight_job_created",
        {"proposed_job_id": "job-1"},
    )
    reply = compose_github_workflow_rerun_route_reply(
        "rerun the failed GitHub workflow",
        session_id="ctx-rerun",
    )
    assert reply is not None
    body, intent, meta = reply
    assert "Which GitHub repo" not in body
    assert meta.get("target_name") == "pilotmain/aethos"
    assert get_pending_rerun_intent("ctx-rerun") is None
    mock_preflight.assert_called_once()


def test_no_active_context_stores_pending_rerun_intent() -> None:
    reply = compose_github_workflow_rerun_route_reply(
        "rerun the failed GitHub workflow",
        session_id="pending-session",
    )
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "github_workflow_rerun_pending_repo"
    assert "Which GitHub repo should I check for failed workflow runs?" in body
    assert "pilotmain/aethos" in body
    pending = get_pending_rerun_intent("pending-session")
    assert pending is not None
    assert pending["type"] == "github_workflow_rerun"
    assert pending["awaiting"] == "repo"


@patch("aethos_core.chat.mutation_preflight_prompts.create_mutation_preflight_job_reply")
def test_repo_reply_continues_rerun_planning(mock_preflight, mutation_enabled) -> None:
    compose_github_workflow_rerun_route_reply(
        "rerun the failed GitHub workflow",
        session_id="continue-session",
    )
    mock_preflight.return_value = (
        "Created governed GitHub workflow rerun preflight `job-2`.",
        "mutation_preflight_job_created",
        {"proposed_job_id": "job-2"},
    )
    assert is_pending_rerun_repo_reply("pilotmain/aethos", session_id="continue-session")
    reply = compose_github_workflow_rerun_route_reply("pilotmain/aethos", session_id="continue-session")
    assert reply is not None
    body, intent, meta = reply
    assert intent == "mutation_preflight_job_created"
    assert meta.get("target_name") == "pilotmain/aethos"
    assert get_pending_rerun_intent("continue-session") is None
    mock_preflight.assert_called_once()
    assert "pilotmain/aethos" in mock_preflight.call_args.args[0]


def test_readonly_router_yields_to_rerun_intent() -> None:
    assert classify_github_readonly_intent("rerun the failed GitHub workflow") is None
    assert compose_github_readonly_route_reply("rerun the failed GitHub workflow") is None


@patch("aethos_core.chat.mutation_preflight_prompts.create_mutation_preflight_job_reply")
def test_no_generic_guidance_for_repo_reply(mock_preflight, mutation_enabled) -> None:
    compose_github_workflow_rerun_route_reply(
        "rerun the failed GitHub workflow",
        session_id="no-generic",
    )
    mock_preflight.return_value = (
        "Created governed GitHub workflow rerun preflight `job-3`.",
        "mutation_preflight_job_created",
        {"proposed_job_id": "job-3"},
    )
    reply = compose_github_workflow_rerun_route_reply("pilotmain/aethos", session_id="no-generic")
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "mutation_preflight_job_created"
    assert "I can run GitHub live diagnostics" not in body
    assert "Which GitHub repo should I inspect?" not in body


@patch("aethos_core.chat.mutation_preflight_prompts.create_mutation_preflight_job_reply", return_value=None)
def test_no_failed_workflow_gives_clear_answer(_mock_preflight, mutation_enabled) -> None:
    save_github_context_from_evidence("no-fail", _diagnostic_evidence(failed=False))
    with patch(
        "aethos_core.providers.github.mutations.workflow_rerun_preflight.discover_workflow_rerun_from_readonly_substrate",
        return_value={"ok": False, "error": "none"},
    ):
        reply = compose_github_workflow_rerun_route_reply(
            "rerun the failed GitHub workflow",
            session_id="no-fail",
        )
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "github_workflow_rerun_no_failed_workflow"
    assert "pilotmain/aethos" in body
    assert "no failed workflow run is available" in body
