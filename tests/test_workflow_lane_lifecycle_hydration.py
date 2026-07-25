# SPDX-License-Identifier: Apache-2.0
"""Fix 88 — Durable workflow execution lifecycle hydration tests."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.providers.github.context.github_context_store import clear_github_context_for_tests
from aethos_core.providers.github.workflow_creation.workflow_creation_context import clear_for_tests as clear_creation_ctx
from aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context import (
    clear_runtime_context_for_tests,
)
from aethos_core.providers.github.workflow_lane.workflow_lane_lifecycle import (
    clear_lifecycle_for_tests,
    hydrate_workflow_lane_context,
    list_recent_workflow_lanes,
    load_latest_workflow_lane_state,
    persist_workflow_lane_state,
)
from aethos_core.providers.github.workflow_lane.workflow_lane_router import (
    clear_for_tests as clear_lane,
    clear_memory_cache_for_tests,
    route_workflow_lane,
)
from aethos_core.runtime.jobs import job_store


def setup_function() -> None:
    clear_github_context_for_tests()
    clear_runtime_context_for_tests()
    clear_creation_ctx()
    clear_lane()
    clear_lifecycle_for_tests()
    job_store.clear_for_tests()


def _blocked_state(session_id: str = "original-session") -> dict:
    return {
        "repo": "pilotmain/aethos",
        "file_path": ".github/workflows/ci.yml",
        "base_branch": "main",
        "branch": "add-ci-workflow",
        "proposal_yaml": "name: CI\n",
        "stage": "execution_blocked",
        "blocker": "missing_github_mutation_credential",
        "last_failed_step": "credential_resolution",
        "branch_created": False,
        "file_committed": False,
        "pr_opened": False,
        "workflow_run_triggered": False,
        "execution_attempts": 1,
    }


def test_persist_writes_global_index() -> None:
    persist_workflow_lane_state("sess-a", _blocked_state("sess-a"))
    entries = list_recent_workflow_lanes(limit=5)
    assert len(entries) >= 1
    assert entries[0]["session_id"] == "sess-a"
    assert entries[0]["stage"] == "execution_blocked"


def test_hydration_after_simulated_restart() -> None:
    """New session_id with empty memory cache still resolves from global index."""
    persist_workflow_lane_state("old-session", _blocked_state("old-session"))
    clear_memory_cache_for_tests()

    state = load_latest_workflow_lane_state(session_id="brand-new-session")
    assert state is not None
    assert state["stage"] == "execution_blocked"
    assert state["blocker"] == "missing_github_mutation_credential"


def test_followup_after_restart_uses_durable_state() -> None:
    persist_workflow_lane_state("persisted", _blocked_state("persisted"))
    clear_memory_cache_for_tests()

    hydrate_workflow_lane_context(session_id="telegram-new-123")
    result = route_workflow_lane("what completed successfully?", session_id="telegram-new-123")
    assert result is not None
    body, intent, meta = result
    assert intent == "workflow_execution_blocked_followup"
    assert "Proposal generated" in body
    assert "Branch creation" in body
    assert meta.get("workflow_lane_hydrated") == "true"
    assert "active_thread" in (meta.get("blocked_routes") or "")


def test_what_failed_after_restart() -> None:
    persist_workflow_lane_state("p1", _blocked_state())
    clear_memory_cache_for_tests()
    hydrate_workflow_lane_context(session_id="fresh")
    result = route_workflow_lane("what failed?", session_id="fresh")
    assert result is not None
    body, _, _ = result
    assert "credential resolution" in body.lower()
    assert "repo write access" in body.lower()


def test_can_we_safely_retry_after_restart() -> None:
    persist_workflow_lane_state("p2", _blocked_state())
    clear_memory_cache_for_tests()
    hydrate_workflow_lane_context(session_id="fresh2")
    result = route_workflow_lane("can we safely retry?", session_id="fresh2")
    assert result is not None
    body, _, _ = result
    assert "safe retry" in body.lower()
    assert "no duplicate-risk" in body.lower() or "duplicate" in body.lower()


def test_resume_execution_after_restart() -> None:
    persist_workflow_lane_state("p3", _blocked_state())
    clear_memory_cache_for_tests()
    hydrate_workflow_lane_context(session_id="fresh3")
    result = route_workflow_lane("resume execution", session_id="fresh3")
    assert result is not None
    body, _, _ = result
    assert "credential resolution" in body.lower()
    assert "retry approval" in body.lower()


@patch("aethos_core.operations.orchestration.provider_runtime.resolve_execution_auth", lambda **kw: {})
@patch("aethos_core.operations.orchestration.provider_runtime.get_provider_api_token", lambda **kw: None)
def test_resolve_chat_turn_hydrates_blocked_lifecycle() -> None:
    persist_workflow_lane_state("live-old", _blocked_state("live-old"))
    clear_memory_cache_for_tests()

    r = resolve_chat_turn(
        "did the PR open?",
        session_id="completely-new-session",
        apply_relational_layer=False,
    )
    assert r.intent == "workflow_execution_blocked_followup"
    assert r.meta.get("route_id") == "github_workflow_lane"
    assert "PR did not open" in r.reply or "did not open" in r.reply
    assert "active operational thread" not in r.reply.lower()
