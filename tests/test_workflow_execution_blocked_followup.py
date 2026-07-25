# SPDX-License-Identifier: Apache-2.0
"""Fix 85 — Workflow Execution Blocked-State Follow-Up tests."""

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


def _setup_blocked(session_id: str = "blocked") -> None:
    """Drive through proposal → plan → approve (no token) → execution_blocked."""
    route_workflow_lane("draft workflow proposal", session_id=session_id)
    route_workflow_lane("create this workflow file", session_id=session_id)
    with patch("aethos_core.operations.orchestration.provider_runtime.resolve_execution_auth", lambda **kw: {}), \
         patch("aethos_core.operations.orchestration.provider_runtime.get_provider_api_token", lambda **kw: None):
        route_workflow_lane("approve", session_id=session_id)
    state = get_workflow_lane_state(session_id=session_id)
    assert state is not None
    assert state["stage"] == "execution_blocked"


# ─── Blocked State Stored ────────────────────────────────────────────────────

def test_approve_missing_credential_stores_blocked_state() -> None:
    _setup_blocked("store-test")
    state = get_workflow_lane_state(session_id="store-test")
    assert state["stage"] == "execution_blocked"
    assert state["blocker"] == "missing_github_mutation_credential"
    assert state["pr_opened"] is False
    assert state["branch_created"] is False
    assert state["file_committed"] is False
    assert state["workflow_run_triggered"] is False


# ─── Follow-Up: Did the PR open? ────────────────────────────────────────────

def test_did_pr_open_answers_no_with_blocker() -> None:
    _setup_blocked("pr-q")
    result = route_workflow_lane("did the PR open?", session_id="pr-q")
    assert result is not None
    body, intent, meta = result
    assert "No" in body
    assert "PR did not open" in body
    assert meta["workflow_lane_stage"] == "execution_blocked"


# ─── Follow-Up: Did the workflow run? ────────────────────────────────────────

def test_did_workflow_run_answers_no_with_blocker() -> None:
    _setup_blocked("wf-q")
    result = route_workflow_lane("did the workflow run?", session_id="wf-q")
    assert result is not None
    body, intent, meta = result
    assert "No" in body
    assert "workflow run" in body.lower()
    assert "did not" in body.lower() or "not triggered" in body.lower()


# ─── Follow-Up: Where is the failure boundary? ──────────────────────────────

def test_failure_boundary_answers_pre_mutation() -> None:
    _setup_blocked("boundary-q")
    result = route_workflow_lane("where is the failure boundary?", session_id="boundary-q")
    assert result is not None
    body, intent, meta = result
    assert "before GitHub mutation" in body
    assert "No branch was created" in body
    assert "No file was committed" in body
    assert "No PR was opened" in body


# ─── Follow-Up: What credential is missing? ─────────────────────────────────

def test_what_credential_is_missing_gives_guidance() -> None:
    _setup_blocked("cred-q")
    result = route_workflow_lane("what credential is missing?", session_id="cred-q")
    assert result is not None
    body, intent, meta = result
    assert intent == "workflow_execution_credential_guidance"
    assert "repo" in body.lower()
    assert "write access" in body.lower()
    assert "add-ci-workflow" in body
    assert "No mutation has been performed" in body


# ─── Cancel After Blocked Clears State ──────────────────────────────────────

def test_cancel_after_blocked_clears_state() -> None:
    _setup_blocked("cancel-blocked")
    result = route_workflow_lane("cancel", session_id="cancel-blocked")
    assert result is not None
    body, intent, meta = result
    assert intent == "workflow_creation_cancelled"
    assert "Cancelled" in body
    assert get_workflow_lane_state(session_id="cancel-blocked") is None


# ─── Follow-ups don't fire without blocked state ────────────────────────────

def test_followups_do_not_fire_without_blocked_state() -> None:
    result = route_workflow_lane("did the PR open?", session_id="no-state")
    assert result is None


# ─── Full lifecycle via resolve_chat_turn ────────────────────────────────────

def test_resolve_chat_turn_blocked_followup() -> None:
    sid = "turn-blocked"
    _setup_blocked(sid)

    r = resolve_chat_turn("did the PR open?", session_id=sid, apply_relational_layer=False)
    assert r.intent == "workflow_execution_blocked_followup"
    assert r.meta.get("route_id") == "github_workflow_lane"
    assert "PR did not open" in r.reply

    r2 = resolve_chat_turn("what credential is missing?", session_id=sid, apply_relational_layer=False)
    assert r2.intent == "workflow_execution_credential_guidance"
    assert "repo" in r2.reply.lower()
