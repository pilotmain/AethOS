# SPDX-License-Identifier: Apache-2.0
"""Fix 87 — Partial Execution Recovery + Idempotent Retry tests."""

from __future__ import annotations

from unittest.mock import patch

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


def _mock_auth(**kw):
    return {"credential_id": "x"}


def _mock_token(**kw):
    return "ghp_test"


def _setup_plan(session_id: str = "partial") -> None:
    route_workflow_lane("draft workflow proposal", session_id=session_id)
    route_workflow_lane("create this workflow file", session_id=session_id)


# ─── Executor Idempotency Tests ──────────────────────────────────────────────

def test_executor_skips_branch_if_already_created() -> None:
    """If prior_progress says branch_created=True, skip branch creation."""
    call_log = []

    def mock_request(token, method, path, *, params=None, json_body=None):
        call_log.append((method, path))
        if method == "GET" and "contents" in path:
            return {"ok": False, "data": None, "http_status": 404}
        if method == "PUT" and "contents" in path:
            return {"ok": True, "data": {"commit": {"sha": "c_sha"}}, "http_status": 201}
        if method == "POST" and "pulls" in path:
            return {"ok": True, "data": {"html_url": "https://github.com/x/y/pull/1", "number": 1}, "http_status": 201}
        return {"ok": True, "data": {}, "http_status": 200}

    prior = {"branch_created": True, "branch_name": "add-ci-workflow", "execution_attempts": 1}

    with patch("aethos_core.providers.github.workflow_lane.workflow_lane_executor.request_github", mock_request):
        result = execute_workflow_file_creation(
            "ghp_tok",
            repo="pilotmain/aethos",
            file_path=".github/workflows/ci.yml",
            branch="add-ci-workflow",
            base_branch="main",
            yaml_content="name: CI\n",
            prior_progress=prior,
        )

    assert result["ok"]
    assert result["progress"]["branch_created"] is True
    assert result["progress"]["execution_attempts"] == 2
    branch_calls = [c for c in call_log if "git/refs" in c[1]]
    assert len(branch_calls) == 0


def test_executor_skips_file_if_already_on_branch() -> None:
    """If file already exists on branch, mark as committed without re-creating."""
    def mock_request(token, method, path, *, params=None, json_body=None):
        if method == "GET" and "contents" in path and "add-ci-workflow" in str(params or {}):
            return {"ok": True, "data": {"sha": "file_sha_123"}, "http_status": 200}
        if method == "GET" and "contents" in path:
            return {"ok": False, "data": None, "http_status": 404}
        if method == "GET" and "git/ref/heads/main" in path:
            return {"ok": True, "data": {"object": {"sha": "base"}}, "http_status": 200}
        if method == "POST" and "git/refs" in path:
            return {"ok": True, "data": {}, "http_status": 201}
        if method == "POST" and "pulls" in path:
            return {"ok": True, "data": {"html_url": "https://github.com/x/y/pull/2", "number": 2}, "http_status": 201}
        return {"ok": True, "data": {}, "http_status": 200}

    with patch("aethos_core.providers.github.workflow_lane.workflow_lane_executor.request_github", mock_request):
        result = execute_workflow_file_creation(
            "ghp_tok",
            repo="pilotmain/aethos",
            file_path=".github/workflows/ci.yml",
            branch="add-ci-workflow",
            base_branch="main",
            yaml_content="name: CI\n",
        )

    assert result["ok"]
    assert result["progress"]["file_committed"] is True
    assert result["progress"]["file_reused"] is True


def test_executor_reuses_existing_pr() -> None:
    """If PR already exists, reuse it."""
    def mock_request(token, method, path, *, params=None, json_body=None):
        if method == "GET" and "contents" in path:
            return {"ok": False, "data": None, "http_status": 404}
        if method == "GET" and "git/ref/heads/main" in path:
            return {"ok": True, "data": {"object": {"sha": "base"}}, "http_status": 200}
        if method == "POST" and "git/refs" in path:
            return {"ok": True, "data": {}, "http_status": 201}
        if method == "PUT" and "contents" in path:
            return {"ok": True, "data": {"commit": {"sha": "c_sha"}}, "http_status": 201}
        if method == "POST" and "pulls" in path:
            return {"ok": False, "error": "A pull request already exists", "http_status": 422}
        if method == "GET" and "pulls" in path:
            return {"ok": True, "data": [{"html_url": "https://github.com/x/y/pull/99", "number": 99}], "http_status": 200}
        return {"ok": True, "data": {}, "http_status": 200}

    with patch("aethos_core.providers.github.workflow_lane.workflow_lane_executor.request_github", mock_request):
        result = execute_workflow_file_creation(
            "ghp_tok",
            repo="pilotmain/aethos",
            file_path=".github/workflows/ci.yml",
            branch="add-ci-workflow",
            base_branch="main",
            yaml_content="name: CI\n",
        )

    assert result["ok"]
    assert result["progress"]["pr_opened"] is True
    assert result["progress"]["pr_reused"] is True
    assert "pull/99" in result["pr_url"]


# ─── Partial Failure Persists Progress ───────────────────────────────────────

def test_partial_failure_at_file_commit_persists_progress() -> None:
    _setup_plan("partial-file")

    def mock_request(token, method, path, *, params=None, json_body=None):
        if method == "GET" and "contents" in path:
            return {"ok": False, "data": None, "http_status": 404}
        if method == "GET" and "git/ref/heads/main" in path:
            return {"ok": True, "data": {"object": {"sha": "base"}}, "http_status": 200}
        if method == "POST" and "git/refs" in path:
            return {"ok": True, "data": {}, "http_status": 201}
        if method == "PUT" and "contents" in path:
            return {"ok": False, "error": "Server error", "http_status": 500}
        return {"ok": True, "data": {}, "http_status": 200}

    with patch("aethos_core.operations.orchestration.provider_runtime.resolve_execution_auth", _mock_auth), \
         patch("aethos_core.operations.orchestration.provider_runtime.get_provider_api_token", _mock_token), \
         patch("aethos_core.providers.github.workflow_lane.workflow_lane_executor.request_github", mock_request):
        route_workflow_lane("approve", session_id="partial-file")

    state = get_workflow_lane_state(session_id="partial-file")
    progress = state.get("execution_progress", {})
    assert progress["branch_created"] is True
    assert progress["file_committed"] is False
    assert progress["last_failed_step"] == "create_file"
    assert progress["execution_attempts"] == 1


# ─── Retry Resumes From Last Step ────────────────────────────────────────────

def test_retry_resumes_from_partial_progress() -> None:
    _setup_plan("resume")

    # First attempt: branch ok, file fails
    def mock_fail(token, method, path, *, params=None, json_body=None):
        if method == "GET" and "contents" in path:
            return {"ok": False, "data": None, "http_status": 404}
        if method == "GET" and "git/ref/heads/main" in path:
            return {"ok": True, "data": {"object": {"sha": "base"}}, "http_status": 200}
        if method == "POST" and "git/refs" in path:
            return {"ok": True, "data": {}, "http_status": 201}
        if method == "PUT" and "contents" in path:
            return {"ok": False, "error": "timeout", "http_status": None}
        return {"ok": True, "data": {}, "http_status": 200}

    with patch("aethos_core.operations.orchestration.provider_runtime.resolve_execution_auth", _mock_auth), \
         patch("aethos_core.operations.orchestration.provider_runtime.get_provider_api_token", _mock_token), \
         patch("aethos_core.providers.github.workflow_lane.workflow_lane_executor.request_github", mock_fail):
        route_workflow_lane("approve", session_id="resume")

    # Second attempt: file and PR succeed; branch already exists
    def mock_ok(token, method, path, *, params=None, json_body=None):
        if method == "GET" and "contents" in path:
            return {"ok": False, "data": None, "http_status": 404}
        if method == "GET" and "git/ref/heads/main" in path:
            return {"ok": True, "data": {"object": {"sha": "base"}}, "http_status": 200}
        if method == "POST" and "git/refs" in path:
            return {"ok": False, "error": "Reference already exists", "http_status": 422}
        if method == "PUT" and "contents" in path:
            return {"ok": True, "data": {"commit": {"sha": "new_sha"}}, "http_status": 201}
        if method == "POST" and "pulls" in path:
            return {"ok": True, "data": {"html_url": "https://github.com/x/y/pull/7", "number": 7}, "http_status": 201}
        return {"ok": True, "data": {}, "http_status": 200}

    with patch("aethos_core.operations.orchestration.provider_runtime.resolve_execution_auth", _mock_auth), \
         patch("aethos_core.operations.orchestration.provider_runtime.get_provider_api_token", _mock_token), \
         patch("aethos_core.providers.github.workflow_lane.workflow_lane_executor.request_github", mock_ok):
        result = route_workflow_lane("retry approval", session_id="resume")

    assert result is not None
    body, intent, meta = result
    assert intent == "workflow_creation_executed"
    state = get_workflow_lane_state(session_id="resume")
    progress = state.get("execution_progress", {})
    assert progress["execution_attempts"] == 2
    assert progress["branch_created"] is True
    assert progress["file_committed"] is True
    assert progress["pr_opened"] is True


# ─── Follow-up: What Completed Successfully? ────────────────────────────────

def test_what_completed_shows_partial_progress() -> None:
    _setup_plan("completed-q")

    def mock_request(token, method, path, *, params=None, json_body=None):
        if method == "GET" and "contents" in path:
            return {"ok": False, "data": None, "http_status": 404}
        if method == "GET" and "git/ref/heads/main" in path:
            return {"ok": True, "data": {"object": {"sha": "base"}}, "http_status": 200}
        if method == "POST" and "git/refs" in path:
            return {"ok": True, "data": {}, "http_status": 201}
        if method == "PUT" and "contents" in path:
            return {"ok": True, "data": {"commit": {"sha": "c1"}}, "http_status": 201}
        if method == "POST" and "pulls" in path:
            return {"ok": False, "error": "Network error", "http_status": None}
        return {"ok": True, "data": {}, "http_status": 200}

    with patch("aethos_core.operations.orchestration.provider_runtime.resolve_execution_auth", _mock_auth), \
         patch("aethos_core.operations.orchestration.provider_runtime.get_provider_api_token", _mock_token), \
         patch("aethos_core.providers.github.workflow_lane.workflow_lane_executor.request_github", mock_request):
        route_workflow_lane("approve", session_id="completed-q")

    result = route_workflow_lane("what completed successfully?", session_id="completed-q")
    assert result is not None
    body, intent, meta = result
    assert "Branch" in body
    assert "file committed" in body.lower()
    assert "PR creation" in body or "pr_opened" in str(meta)


# ─── Follow-up: Can We Safely Retry? ────────────────────────────────────────

def test_can_we_safely_retry_with_partial_state() -> None:
    _setup_plan("safe-q")

    def mock_request(token, method, path, *, params=None, json_body=None):
        if method == "GET" and "contents" in path:
            return {"ok": False, "data": None, "http_status": 404}
        if method == "GET" and "git/ref/heads/main" in path:
            return {"ok": True, "data": {"object": {"sha": "base"}}, "http_status": 200}
        if method == "POST" and "git/refs" in path:
            return {"ok": True, "data": {}, "http_status": 201}
        if method == "PUT" and "contents" in path:
            return {"ok": False, "error": "timeout", "http_status": None}
        return {"ok": True, "data": {}, "http_status": 200}

    with patch("aethos_core.operations.orchestration.provider_runtime.resolve_execution_auth", _mock_auth), \
         patch("aethos_core.operations.orchestration.provider_runtime.get_provider_api_token", _mock_token), \
         patch("aethos_core.providers.github.workflow_lane.workflow_lane_executor.request_github", mock_request):
        route_workflow_lane("approve", session_id="safe-q")

    result = route_workflow_lane("can we safely retry?", session_id="safe-q")
    assert result is not None
    body, intent, meta = result
    assert "Safe to retry: yes" in body
    assert "Branch already exists" in body
    assert "retry approval" in body.lower() or "approve" in body.lower()


# ─── No Duplicate Branch/File/PR ─────────────────────────────────────────────

def test_no_duplicate_after_full_success() -> None:
    """After successful execution, retry should say already executed."""
    _setup_plan("no-dup")

    def mock_ok(token, method, path, *, params=None, json_body=None):
        if method == "GET" and "contents" in path:
            return {"ok": False, "data": None, "http_status": 404}
        if method == "GET" and "git/ref/heads/main" in path:
            return {"ok": True, "data": {"object": {"sha": "base"}}, "http_status": 200}
        if method == "POST" and "git/refs" in path:
            return {"ok": True, "data": {}, "http_status": 201}
        if method == "PUT" and "contents" in path:
            return {"ok": True, "data": {"commit": {"sha": "c1"}}, "http_status": 201}
        if method == "POST" and "pulls" in path:
            return {"ok": True, "data": {"html_url": "https://github.com/x/y/pull/3", "number": 3}, "http_status": 201}
        return {"ok": True, "data": {}, "http_status": 200}

    with patch("aethos_core.operations.orchestration.provider_runtime.resolve_execution_auth", _mock_auth), \
         patch("aethos_core.operations.orchestration.provider_runtime.get_provider_api_token", _mock_token), \
         patch("aethos_core.providers.github.workflow_lane.workflow_lane_executor.request_github", mock_ok):
        route_workflow_lane("approve", session_id="no-dup")

    result = route_workflow_lane("retry approval", session_id="no-dup")
    assert result is not None
    body, intent, meta = result
    assert intent == "workflow_lane_already_executed"
    assert "already been executed" in body
