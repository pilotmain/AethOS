# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 88 — Railway preflight must not run GitHub workflow lane / discovery."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aethos_core.chat.route_trace import clear_route_traces_for_tests
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.operations.mutations.preflight import run_mutation_preflight
from aethos_core.providers.github.context.github_context_store import clear_github_context_for_tests
from aethos_core.providers.github.workflow_creation.workflow_creation_context import clear_for_tests as clear_creation_ctx
from aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context import (
    clear_runtime_context_for_tests,
)
from aethos_core.providers.github.workflow_lane.workflow_lane_guards import (
    has_github_workflow_lane_intent,
    is_railway_mutation_context,
    should_hydrate_github_workflow_context,
    should_run_github_workflow_lane,
)
from aethos_core.providers.github.workflow_lane.workflow_lane_router import (
    clear_for_tests as clear_lane,
    is_workflow_lane_intent,
    route_workflow_lane,
)
from aethos_core.runtime.jobs import job_store
from aethos_core.task_frame.pending_action import (
    PendingAction,
    clear_pending_actions_for_tests,
    store_pending_action,
)


def setup_function() -> None:
    clear_github_context_for_tests()
    clear_runtime_context_for_tests()
    clear_route_traces_for_tests()
    clear_creation_ctx()
    clear_lane()
    clear_pending_actions_for_tests()
    job_store.clear_for_tests()


def test_railway_restart_not_github_workflow_lane_intent() -> None:
    assert is_railway_mutation_context("restart pilotos-api in railway")
    assert not should_run_github_workflow_lane("restart pilotos-api in railway")
    assert not is_workflow_lane_intent("restart pilotos-api in railway")
    assert not has_github_workflow_lane_intent("restart pilotos-api in railway")


def test_bare_retry_not_workflow_lane_intent() -> None:
    assert not is_workflow_lane_intent("retry")
    assert route_workflow_lane("retry", session_id="railway-retry") is None


def test_railway_preflight_no_unbound_discovery() -> None:
    outcome = run_mutation_preflight(
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "user_request": "restart pilotos-api in railway",
            "target_name": "pilotos-api",
            "target_resolved": True,
            "target": {
                "provider": "railway",
                "project_name": "pilotos",
                "environment": "production",
                "service_name": "pilotos-api",
                "resolved": True,
            },
            "session_id": "railway-preflight",
        },
    )
    assert "discovery" not in outcome.summary.lower()
    assert outcome.provider == "railway"
    assert outcome.operation_type == "restart"


@patch(
    "aethos_core.providers.github.workflow_lane.workflow_lane_lifecycle.hydrate_workflow_lane_context",
)
@patch(
    "aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context.hydrate_workflow_discovery_context",
)
def test_railway_restart_skips_github_hydration(mock_disc: MagicMock, mock_lane: MagicMock) -> None:
    from aethos_core.providers.github.workflow_lane.workflow_lane_guards import (
        maybe_hydrate_github_workflow_context,
    )

    maybe_hydrate_github_workflow_context(
        text="restart pilotos-api in railway",
        session_id="iso-1",
    )
    mock_disc.assert_not_called()
    mock_lane.assert_not_called()


def test_github_proposal_still_hydrates() -> None:
    assert should_hydrate_github_workflow_context(
        text="draft workflow proposal",
        session_id="iso-2",
    )
    assert has_github_workflow_lane_intent("draft workflow proposal")


@patch("aethos_core.task_frame.confirmation_continuation.create_governed_retry_preflight")
def test_retry_after_railway_preflight_routes_railway(mock_retry) -> None:
    mock_retry.return_value = (
        "Retrying the latest Railway restart preflight for pilotos / production / pilotos-api.",
        "pending_action_preflight_created",
        {"provider": "railway", "route_id": "retry_active_operation"},
    )
    store_pending_action(
        PendingAction(
            session_id="railway-retry-sess",
            provider="railway",
            project="pilotos",
            environment="production",
            service="pilotos-api",
            operation="restart",
            next_action="create_mutation_preflight",
            status="awaiting_user_confirmation",
        ),
    )
    result = resolve_chat_turn("retry", session_id="railway-retry-sess", apply_relational_layer=False)
    assert result.intent == "pending_action_preflight_created"
    assert "Railway" in result.reply
    assert "No pending GitHub workflow creation plan" not in result.reply
    mock_retry.assert_called_once()


@patch("aethos_core.providers.github.workflow_lane.workflow_lane_router._handle_proposal")
def test_draft_workflow_proposal_still_uses_lane(mock_proposal) -> None:
    mock_proposal.return_value = ("proposal yaml", "workflow_discovery_proposal", {"route_id": "github_workflow_lane"})
    result = resolve_chat_turn("draft workflow proposal", session_id="iso-proposal", apply_relational_layer=False)
    assert result.intent == "workflow_discovery_proposal"
    mock_proposal.assert_called_once()
