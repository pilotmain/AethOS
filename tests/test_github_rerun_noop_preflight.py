# SPDX-License-Identifier: Apache-2.0
"""GitHub workflow rerun no-op preflight tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.mutation_preflight_prompts import create_mutation_preflight_job_reply
from aethos_core.jobs.job_approval_guidance import build_no_action_preflight_metadata, get_job_approval_guidance
from aethos_core.operations.intents import infer_operation_preflight_intent
from aethos_core.operations.mutations.preflight import run_mutation_preflight
from aethos_core.providers.github.context.github_context_store import (
    clear_github_context_for_tests,
    save_github_context_from_evidence,
)
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store
from tests.job_test_utils import drain_job_executor


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


def _green_evidence() -> dict:
    return {
        "repository": "pilotmain/aethos",
        "repo": {"full_name": "pilotmain/aethos", "default_branch": "main"},
        "branch": {"branch": "main", "sha": "abc123def456"},
        "commits": {"commits": [{"sha": "abc123def456", "message": "fix", "author": "raya"}]},
        "checks": {"ok": True, "failed_count": 0, "checks": []},
        "workflow_runs": {"ok": True, "runs": [{"id": 1, "name": "CI", "conclusion": "success"}]},
        "workflow_diagnostic": {"ok": True, "latest_failed_run": None},
    }


def _failed_evidence() -> dict:
    return {
        "repository": "pilotmain/aethos",
        "repo": {"full_name": "pilotmain/aethos", "default_branch": "main"},
        "branch": {"branch": "main", "sha": "abc123def456"},
        "commits": {"commits": [{"sha": "abc123def456", "message": "fix", "author": "raya"}]},
        "checks": {"ok": True, "failed_count": 1, "checks": []},
        "workflow_runs": {"ok": True, "runs": []},
        "workflow_diagnostic": {
            "ok": True,
            "latest_failed_run": {
                "id": 123456,
                "name": "CI",
                "run_number": 42,
                "head_branch": "main",
                "head_sha": "abc123def456",
                "status": "completed",
                "conclusion": "failure",
            },
        },
    }


def test_intent_title_has_no_duplicate_mutation() -> None:
    inferred = infer_operation_preflight_intent("rerun the failed GitHub workflow")
    assert inferred is not None
    title, _job_type, _params = inferred
    assert title == "GitHub workflow rerun preflight"
    assert "mutation mutation" not in title


@patch("aethos_core.operations.mutations.preflight._mutation_provider_auth_block", return_value=None)
def test_no_failed_workflow_preflight_is_no_action(_auth, mutation_enabled) -> None:
    save_github_context_from_evidence("noop-pf", _green_evidence())
    with patch(
        "aethos_core.providers.github.mutations.workflow_rerun_preflight.discover_workflow_rerun_from_readonly_substrate",
        return_value={"ok": False, "error": "none"},
    ):
        outcome = run_mutation_preflight(
            job_type="mutation_preflight",
            params={
                "user_request": "rerun the failed GitHub workflow",
                "provider": "github",
                "operation_type": "workflow_rerun",
                "session_id": "noop-pf",
            },
        )
    assert outcome.preflight_status == "no_action_available"
    assert "No approval is required" in outcome.full_result
    assert "Mutation preflight" not in outcome.full_result
    assert "mutation mutation" not in outcome.summary.lower()


def test_no_failed_workflow_chat_reply_requires_no_approval(mutation_enabled) -> None:
    save_github_context_from_evidence("noop-chat", _green_evidence())
    with patch(
        "aethos_core.providers.github.mutations.workflow_rerun_preflight.discover_workflow_rerun_from_readonly_substrate",
        return_value={"ok": False, "error": "none"},
    ):
        reply = create_mutation_preflight_job_reply(
            "rerun the failed GitHub workflow",
            session_id="noop-chat",
        )
    assert reply is not None
    body, intent, meta = reply
    assert intent == "github_workflow_rerun_no_action"
    assert meta.get("preflight_status") == "no_action_available"
    assert "No approval is required" in body
    assert "Approve Governed Mutation" not in body


def test_no_action_metadata_not_approvable() -> None:
    meta = build_no_action_preflight_metadata(reason="no failed workflow run found")
    assert meta["approval_required"] is False
    assert meta["ui_action_available"] is False
    assert meta["preflight_status"] == "no_action_available"
    assert meta["no_action_reason"] == "no failed workflow run found"


@patch("aethos_core.operations.mutations.preflight._mutation_provider_auth_block", return_value=None)
def test_failed_workflow_preflight_remains_approvable(_auth, mutation_enabled) -> None:
    save_github_context_from_evidence("approvable-pf", _failed_evidence())
    outcome = run_mutation_preflight(
        job_type="mutation_preflight",
        params={
            "user_request": "rerun the failed GitHub workflow",
            "provider": "github",
            "operation_type": "workflow_rerun",
            "session_id": "approvable-pf",
            "target_name": "pilotmain/aethos",
            "target_status": "resolved",
        },
    )
    assert outcome.preflight_status == "ready_for_mutation_approval"
    assert "Created governed GitHub workflow rerun preflight" in outcome.full_result


@patch("aethos_core.operations.mutations.preflight._mutation_provider_auth_block", return_value=None)
def test_mission_control_not_approvable_for_no_action(_auth, mutation_enabled) -> None:
    save_github_context_from_evidence("noop-mc", _green_evidence())
    job = authority.create_job(
        title="GitHub workflow rerun preflight",
        job_type="mutation_preflight",
        params={
            "user_request": "rerun the failed GitHub workflow",
            "provider": "github",
            "operation_type": "workflow_rerun",
            "session_id": "noop-mc",
        },
        source="test",
        session_id="noop-mc",
        auto_run=True,
    )
    with patch(
        "aethos_core.providers.github.mutations.workflow_rerun_preflight.discover_workflow_rerun_from_readonly_substrate",
        return_value={"ok": False, "error": "none"},
    ):
        drain_job_executor()
    completed = job_store.get(job.id)
    assert completed is not None
    assert completed.params.get("preflight_status") == "no_action_available"
    assert completed.params.get("ui_action_available") is False
    guidance = get_job_approval_guidance(job.id, session_id="noop-mc")
    assert guidance.found is True
    assert guidance.ui_action_available is False
    assert guidance.approval_required is False
    assert guidance.reason == "no failed workflow run found"
