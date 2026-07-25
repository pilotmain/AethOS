# SPDX-License-Identifier: Apache-2.0
"""Connection-status and GitHub-repo queries must route correctly, not be hijacked."""

from __future__ import annotations

import pytest

from aethos_core.failed_service_investigation.global_preemption import (
    _is_connections_status_query,
    should_preempt_to_failed_service,
)
from aethos_core.chat.provider_read_intent import is_provider_read_inventory_request


@pytest.mark.parametrize(
    "prompt",
    [
        "show my connection status for all providers",
        "connection status for all providers",
        "show my connections",
        "check my provider connections",
    ],
)
def test_connection_status_not_failed_service(prompt):
    assert _is_connections_status_query(prompt) is True
    # Must never be claimed by the failed-service investigation lane.
    assert should_preempt_to_failed_service(prompt, session_id="t-conn") is False


def test_real_failed_service_still_preempts_are_unaffected():
    # A genuine connection-status query is excluded, but this guard must not over-match a
    # plain service failure question.
    assert _is_connections_status_query("why did aethos-api fail?") is False


@pytest.mark.parametrize(
    "prompt",
    [
        "which GitHub repos can you access?",
        "list my github repos",
        "what repositories can you reach on github?",
    ],
)
def test_github_repo_listing_is_provider_read(prompt):
    assert is_provider_read_inventory_request(prompt) is True


def test_unscoped_service_status_does_not_default_to_vercel():
    """'is aethos-api healthy? latest deployment status' must NOT create a Vercel preflight —
    aethos-api is a Railway service; defer to the agent which checks both inventories."""
    from aethos_core.operations.intents import infer_operation_preflight_intent

    result = infer_operation_preflight_intent(
        "is the aethos-api service healthy? show its latest deployment status"
    )
    assert result is None


def test_explicit_vercel_deployments_still_preflights():
    from aethos_core.operations.intents import infer_operation_preflight_intent

    result = infer_operation_preflight_intent("list my vercel deployments")
    assert result is not None
    assert result[2].get("provider") == "vercel"


@pytest.mark.parametrize(
    "prompt",
    [
        "show recent deployment logs for my Vercel project",
        "show me the logs for my railway service",
    ],
)
def test_logs_request_not_inventory(prompt):
    assert is_provider_read_inventory_request(prompt) is False


def test_projects_request_still_inventory():
    assert is_provider_read_inventory_request("show my vercel projects") is True
