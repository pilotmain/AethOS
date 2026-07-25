# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 93B — lazy lane hydration isolation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from aethos_core.chat.lane_hydration import (
    maybe_hydrate_lane_contexts,
    should_hydrate_browser_context,
    should_hydrate_railway_deployment_plan_context,
)


def test_browser_hydration_not_called_for_railway_plan() -> None:
    assert should_hydrate_railway_deployment_plan_context(
        "create railway deployment plan for pilotmain/aethos"
    )
    assert not should_hydrate_browser_context(
        "create railway deployment plan for pilotmain/aethos"
    )


@patch("aethos_core.browser_observation.browser_observation_lifecycle.hydrate_browser_observation_context")
@patch(
    "aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context.hydrate_workflow_discovery_context",
)
@patch("aethos_core.providers.github.workflow_lane.workflow_lane_lifecycle.hydrate_workflow_lane_context")
def test_github_hydration_not_called_for_railway_restart(
    mock_lane: MagicMock,
    mock_disc: MagicMock,
    mock_browser: MagicMock,
) -> None:
    maybe_hydrate_lane_contexts(text="restart pilotos-api in railway", session_id="lazy-1")
    mock_disc.assert_not_called()
    mock_lane.assert_not_called()
    mock_browser.assert_not_called()


@patch("aethos_core.browser_observation.browser_observation_lifecycle.hydrate_browser_observation_context")
@patch(
    "aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context.hydrate_workflow_discovery_context",
)
def test_browser_hydration_not_called_for_railway_plan(
    mock_disc: MagicMock,
    mock_browser: MagicMock,
) -> None:
    maybe_hydrate_lane_contexts(
        text="create railway deployment plan for pilotmain/aethos in pilotos / production",
        session_id="lazy-2",
    )
    mock_browser.assert_not_called()
    mock_disc.assert_not_called()
