# SPDX-License-Identifier: Apache-2.0
"""Fix 84 — Governed Workflow File Execution tests."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.providers.github.context.github_context_store import clear_github_context_for_tests
from aethos_core.providers.github.workflow_creation.workflow_creation_context import clear_for_tests as clear_creation_ctx
from aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context import (
    clear_runtime_context_for_tests,
)
from aethos_core.providers.github.workflow_lane.workflow_lane_executor import execute_workflow_file_creation
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


def _setup_creation_plan_ready(session_id: str = "exec-test") -> None:
    route_workflow_lane("draft workflow proposal", session_id=session_id)
    route_workflow_lane("create this workflow file", session_id=session_id)
    state = get_workflow_lane_state(session_id=session_id)
    assert state is not None
    assert state["stage"] == "creation_plan_ready"


# ─── Approve Intent Detection ────────────────────────────────────────────────

def test_approve_not_detected_without_state() -> None:
    from aethos_core.providers.github.workflow_lane.workflow_lane_router import is_workflow_lane_intent

    clear_lane()
    assert not is_workflow_lane_intent("approve")


def test_approve_detected_with_creation_plan_ready() -> None:
    from aethos_core.providers.github.workflow_lane.workflow_lane_router import is_workflow_lane_intent

    _setup_creation_plan_ready("approve-detect")
    assert is_workflow_lane_intent("approve")


# ─── Approve Executes Plan ───────────────────────────────────────────────────

def _mock_execute_success(*args, **kwargs):
    return {
        "ok": True,
        "detail": "Workflow file created on `add-ci-workflow` and PR opened to `main`.",
        "pr_url": "https://github.com/pilotmain/aethos/pull/42",
        "pr_number": 42,
        "commit_sha": "abc123def456",
        "branch": "add-ci-workflow",
        "reused_pr": False,
        "operation": "workflow_file_creation",
        "risk_tier": "T2",
    }


def _mock_auth(*args, **kwargs):
    return {"credential_id": "test-cred", "ok": True}


def _mock_token(*args, **kwargs):
    return "ghp_test_token_1234"


_EXECUTOR_PATCH = "aethos_core.providers.github.workflow_lane.workflow_lane_executor.execute_workflow_file_creation"


@patch(_EXECUTOR_PATCH, _mock_execute_success)
@patch("aethos_core.operations.orchestration.provider_runtime.resolve_execution_auth", _mock_auth)
@patch("aethos_core.operations.orchestration.provider_runtime.get_provider_api_token", _mock_token)
def test_approve_executes_branch_file_pr_flow() -> None:
    _setup_creation_plan_ready("exec-approve")
    result = route_workflow_lane("approve", session_id="exec-approve")
    assert result is not None
    body, intent, meta = result
    assert intent == "workflow_creation_executed"
    assert meta["workflow_lane_stage"] == "executed"
    assert "executed successfully" in body
    assert "add-ci-workflow" in body
    assert "pull/42" in body or "#42" in body
    state = get_workflow_lane_state(session_id="exec-approve")
    assert state is not None
    assert state["stage"] == "executed"


# ─── Direct Main Blocked (Even After Approval) ──────────────────────────────

def test_direct_main_still_blocked_after_plan() -> None:
    _setup_creation_plan_ready("exec-main")
    result = route_workflow_lane("push the workflow to main", session_id="exec-main")
    assert result is not None
    body, intent, meta = result
    assert "will not" in body
    assert "T3" in body


# ─── No Mutation Before Approval ─────────────────────────────────────────────

def test_no_mutation_before_approval() -> None:
    _setup_creation_plan_ready("no-mutate")
    state = get_workflow_lane_state(session_id="no-mutate")
    assert state is not None
    assert state["stage"] == "creation_plan_ready"
    assert "execution_result" not in state


# ─── File Exists Blocks Overwrite ────────────────────────────────────────────

def test_file_exists_blocks_overwrite() -> None:
    def mock_request(token, method, path, *, params=None, json_body=None):
        if method == "GET" and "contents" in path:
            return {"ok": True, "data": {"sha": "existing_sha"}, "http_status": 200}
        return {"ok": True, "data": {}, "http_status": 200}

    with patch("aethos_core.providers.github.workflow_lane.workflow_lane_executor.request_github", mock_request):
        result = execute_workflow_file_creation(
            "ghp_test",
            repo="pilotmain/aethos",
            file_path=".github/workflows/ci.yml",
            branch="add-ci-workflow",
            base_branch="main",
            yaml_content="name: CI\n",
        )
    assert not result["ok"]
    assert "already exists" in result["detail"]
    assert result["step"] == "file_exists_check"


# ─── Branch Conflict Handled ────────────────────────────────────────────────

def test_branch_conflict_reuses_existing() -> None:
    call_count = {"n": 0}

    def mock_request(token, method, path, *, params=None, json_body=None):
        if method == "GET" and "contents" in path:
            return {"ok": False, "data": None, "http_status": 404}
        if method == "GET" and "git/ref/heads/main" in path:
            return {"ok": True, "data": {"object": {"sha": "base_sha_123"}}, "http_status": 200}
        if method == "POST" and "git/refs" in path:
            return {"ok": False, "error": "Reference already exists", "http_status": 422}
        if method == "GET" and "git/ref/heads/add-ci-workflow" in path:
            return {"ok": True, "data": {"object": {"sha": "branch_sha_456"}}, "http_status": 200}
        if method == "PUT" and "contents" in path:
            call_count["n"] += 1
            return {"ok": True, "data": {"commit": {"sha": "commit_789"}}, "http_status": 201}
        if method == "POST" and "pulls" in path:
            return {"ok": True, "data": {"html_url": "https://github.com/pilotmain/aethos/pull/99", "number": 99}, "http_status": 201}
        return {"ok": True, "data": {}, "http_status": 200}

    with patch("aethos_core.providers.github.workflow_lane.workflow_lane_executor.request_github", mock_request):
        result = execute_workflow_file_creation(
            "ghp_test",
            repo="pilotmain/aethos",
            file_path=".github/workflows/ci.yml",
            branch="add-ci-workflow",
            base_branch="main",
            yaml_content="name: CI\non: push\n",
        )
    assert result["ok"]
    assert call_count["n"] == 1
    assert result["pr_url"] == "https://github.com/pilotmain/aethos/pull/99"


# ─── PR Already Exists ──────────────────────────────────────────────────────

def test_pr_already_exists_returns_link() -> None:
    def mock_request(token, method, path, *, params=None, json_body=None):
        if method == "GET" and "contents" in path:
            return {"ok": False, "data": None, "http_status": 404}
        if method == "GET" and "git/ref/heads/main" in path:
            return {"ok": True, "data": {"object": {"sha": "base_sha"}}, "http_status": 200}
        if method == "POST" and "git/refs" in path:
            return {"ok": True, "data": {"ref": "refs/heads/add-ci-workflow"}, "http_status": 201}
        if method == "PUT" and "contents" in path:
            return {"ok": True, "data": {"commit": {"sha": "c_sha"}}, "http_status": 201}
        if method == "POST" and "pulls" in path:
            return {"ok": False, "error": "A pull request already exists", "http_status": 422}
        if method == "GET" and "pulls" in path:
            return {"ok": True, "data": [{"html_url": "https://github.com/pilotmain/aethos/pull/77", "number": 77}], "http_status": 200}
        return {"ok": True, "data": {}, "http_status": 200}

    with patch("aethos_core.providers.github.workflow_lane.workflow_lane_executor.request_github", mock_request):
        result = execute_workflow_file_creation(
            "ghp_test",
            repo="pilotmain/aethos",
            file_path=".github/workflows/ci.yml",
            branch="add-ci-workflow",
            base_branch="main",
            yaml_content="name: CI\n",
        )
    assert result["ok"]
    assert result["reused_pr"] is True
    assert "pull/77" in result["pr_url"]


# ─── Execution Failure Reported ──────────────────────────────────────────────

@patch("aethos_core.operations.orchestration.provider_runtime.resolve_execution_auth", _mock_auth)
@patch("aethos_core.operations.orchestration.provider_runtime.get_provider_api_token", _mock_token)
def test_execution_failure_reported_cleanly() -> None:
    def mock_execute(*args, **kwargs):
        return {
            "ok": False,
            "detail": "Cannot create branch `add-ci-workflow`: network error",
            "step": "create_branch",
            "operation": "workflow_file_creation",
            "risk_tier": "T2",
        }

    _setup_creation_plan_ready("exec-fail")
    with patch(_EXECUTOR_PATCH, mock_execute):
        result = route_workflow_lane("approve", session_id="exec-fail")
    assert result is not None
    body, intent, meta = result
    assert intent == "workflow_execution_failed"
    assert "failed" in body.lower()
    assert "create_branch" in body


# ─── No Token Configured ────────────────────────────────────────────────────

@patch("aethos_core.operations.orchestration.provider_runtime.resolve_execution_auth", _mock_auth)
@patch("aethos_core.operations.orchestration.provider_runtime.get_provider_api_token", lambda **kw: None)
def test_no_token_reports_auth_failure() -> None:
    _setup_creation_plan_ready("exec-no-token")
    result = route_workflow_lane("approve", session_id="exec-no-token")
    assert result is not None
    body, intent, meta = result
    assert intent == "workflow_execution_blocked"
    assert "credential" in body.lower() or "token" in body.lower()


# ─── Full Lifecycle via resolve_chat_turn ────────────────────────────────────

@patch(_EXECUTOR_PATCH, _mock_execute_success)
@patch("aethos_core.operations.orchestration.provider_runtime.resolve_execution_auth", _mock_auth)
@patch("aethos_core.operations.orchestration.provider_runtime.get_provider_api_token", _mock_token)
def test_full_lifecycle_proposal_to_execution() -> None:
    sid = "full-lifecycle"

    r1 = resolve_chat_turn("draft workflow proposal", session_id=sid, apply_relational_layer=False)
    assert r1.intent == "workflow_discovery_proposal"
    assert "name: CI" in r1.reply

    r2 = resolve_chat_turn("create this workflow file", session_id=sid, apply_relational_layer=False)
    assert r2.intent == "workflow_creation_governed_plan"
    assert "approve" in r2.reply.lower()

    r3 = resolve_chat_turn("approve", session_id=sid, apply_relational_layer=False)
    assert r3.intent == "workflow_creation_executed"
    assert "executed successfully" in r3.reply
    assert "add-ci-workflow" in r3.reply

    state = get_workflow_lane_state(session_id=sid)
    assert state["stage"] == "executed"
