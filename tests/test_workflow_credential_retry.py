# SPDX-License-Identifier: Apache-2.0
"""Fix 86 — Credential Refresh + Retry Approval Flow tests."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.providers.github.context.github_context_store import clear_github_context_for_tests
from aethos_core.providers.github.workflow_creation.workflow_creation_context import clear_for_tests as clear_creation_ctx
from aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context import (
    clear_runtime_context_for_tests,
)
from aethos_core.providers.github.workflow_lane.workflow_lane_router import (
    clear_for_tests as clear_lane,
    get_workflow_lane_state,
    route_workflow_lane,
)
from aethos_core.runtime.jobs import job_store


def setup_function() -> None:
    clear_github_context_for_tests()
    clear_runtime_context_for_tests()
    clear_creation_ctx()
    clear_lane()
    job_store.clear_for_tests()


def _no_token(**kw):
    return None


def _has_token(**kw):
    return "ghp_real_token"


def _mock_auth(**kw):
    return {"credential_id": "test-cred"}


def _mock_execute_success(*args, **kwargs):
    return {
        "ok": True,
        "detail": "Workflow file created.",
        "pr_url": "https://github.com/pilotmain/aethos/pull/55",
        "pr_number": 55,
        "commit_sha": "abc123def",
        "branch": "add-ci-workflow",
        "reused_pr": False,
        "operation": "workflow_file_creation",
        "risk_tier": "T2",
    }


def _setup_blocked(session_id: str = "retry") -> None:
    route_workflow_lane("draft workflow proposal", session_id=session_id)
    route_workflow_lane("create this workflow file", session_id=session_id)
    with patch("aethos_core.operations.orchestration.provider_runtime.resolve_execution_auth", _mock_auth), \
         patch("aethos_core.operations.orchestration.provider_runtime.get_provider_api_token", _no_token):
        route_workflow_lane("approve", session_id=session_id)


# ─── Blocked Approval Persists Plan ─────────────────────────────────────────

def test_blocked_approval_persists_plan() -> None:
    _setup_blocked("persist")
    state = get_workflow_lane_state(session_id="persist")
    assert state is not None
    assert state["stage"] == "execution_blocked"
    assert state["proposal_yaml"]
    assert state["repo"] == "pilotmain/aethos"
    assert state["branch"] == "add-ci-workflow"


# ─── Retry After Credential Refresh Reuses Plan ─────────────────────────────

@patch("aethos_core.providers.github.workflow_lane.workflow_lane_executor.execute_workflow_file_creation", _mock_execute_success)
@patch("aethos_core.operations.orchestration.provider_runtime.resolve_execution_auth", _mock_auth)
@patch("aethos_core.operations.orchestration.provider_runtime.get_provider_api_token", _has_token)
def test_retry_after_credential_refresh_reuses_plan() -> None:
    _setup_blocked("retry-ok")
    result = route_workflow_lane("retry approval", session_id="retry-ok")
    assert result is not None
    body, intent, meta = result
    assert intent == "workflow_creation_executed"
    assert meta["workflow_lane_stage"] == "executed"
    assert "pull/55" in body


@patch("aethos_core.providers.github.workflow_lane.workflow_lane_executor.execute_workflow_file_creation", _mock_execute_success)
@patch("aethos_core.operations.orchestration.provider_runtime.resolve_execution_auth", _mock_auth)
@patch("aethos_core.operations.orchestration.provider_runtime.get_provider_api_token", _has_token)
def test_retry_with_natural_language() -> None:
    _setup_blocked("retry-nl")
    result = route_workflow_lane("I added the GitHub token, retry approval", session_id="retry-nl")
    assert result is not None
    _, intent, _ = result
    assert intent == "workflow_creation_executed"


# ─── Retry With No Credential Still Blocked ─────────────────────────────────

@patch("aethos_core.operations.orchestration.provider_runtime.resolve_execution_auth", _mock_auth)
@patch("aethos_core.operations.orchestration.provider_runtime.get_provider_api_token", _no_token)
def test_retry_with_no_credential_still_blocked() -> None:
    _setup_blocked("retry-no")
    result = route_workflow_lane("retry approval", session_id="retry-no")
    assert result is not None
    body, intent, meta = result
    assert intent == "workflow_execution_blocked"
    assert "credential" in body.lower()
    assert meta["workflow_lane_stage"] == "execution_blocked"


# ─── Retry After Cancel Says No Pending Plan ────────────────────────────────

def test_retry_after_cancel_says_no_pending_plan() -> None:
    _setup_blocked("retry-cancel")
    route_workflow_lane("cancel", session_id="retry-cancel")
    result = route_workflow_lane("retry approval", session_id="retry-cancel")
    assert result is not None
    body, intent, meta = result
    assert intent == "workflow_lane_no_state"
    assert "No pending" in body or "draft workflow proposal" in body


# ─── Retry With No State ────────────────────────────────────────────────────

def test_retry_with_no_state() -> None:
    result = route_workflow_lane("retry approval", session_id="empty")
    assert result is not None
    body, intent, meta = result
    assert intent == "workflow_lane_no_state"
    assert "No pending" in body


# ─── Retry With Proposal Only (Not Plan Ready) ──────────────────────────────

def test_retry_with_proposal_only_not_ready() -> None:
    route_workflow_lane("draft workflow proposal", session_id="early")
    result = route_workflow_lane("retry approval", session_id="early")
    assert result is not None
    body, intent, meta = result
    assert intent == "workflow_lane_not_ready"
    assert "not yet ready" in body


# ─── Intent Detection for Retry Phrases ──────────────────────────────────────

def test_retry_intent_detection() -> None:
    from aethos_core.providers.github.workflow_lane.workflow_lane_router import is_workflow_lane_intent

    positives = [
        "retry approval",
        "I added the GitHub token",
        "approve again",
        "refresh credentials",
        "I configured the token",
    ]
    for phrase in positives:
        assert is_workflow_lane_intent(phrase), f"not detected: {phrase!r}"


# ─── Full Lifecycle via resolve_chat_turn ────────────────────────────────────

@patch("aethos_core.providers.github.workflow_lane.workflow_lane_executor.execute_workflow_file_creation", _mock_execute_success)
@patch("aethos_core.operations.orchestration.provider_runtime.resolve_execution_auth", _mock_auth)
@patch("aethos_core.operations.orchestration.provider_runtime.get_provider_api_token", _has_token)
def test_full_lifecycle_blocked_then_retry_succeeds() -> None:
    sid = "full-retry"
    _setup_blocked(sid)

    r = resolve_chat_turn("I added the GitHub token, retry approval", session_id=sid, apply_relational_layer=False)
    assert r.intent == "workflow_creation_executed"
    assert "executed successfully" in r.reply
    assert r.meta.get("route_id") == "github_workflow_lane"
    assert r.meta.get("workflow_lane_stage") == "executed"
