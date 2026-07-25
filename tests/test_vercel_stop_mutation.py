# SPDX-License-Identifier: Apache-2.0
"""Vercel governed stop — cancel in-flight builds or pause live production."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aethos_core.providers.vercel.operations.mutations_api import stop_project


@pytest.fixture
def mock_project():
    return {"id": "prj_test", "name": "killit", "teamId": "team_abc"}


@pytest.fixture
def mock_deployments_ready():
    return [{"uid": "dpl_ready", "state": "READY"}]


@pytest.fixture
def mock_deployments_building():
    return [{"uid": "dpl_build", "state": "BUILDING"}]


def test_stop_pauses_ready_production(mock_project, mock_deployments_ready):
    with (
        patch(
            "aethos_core.providers.vercel.operations.mutations_api.find_project_by_name",
            return_value=mock_project,
        ),
        patch(
            "aethos_core.providers.vercel.api_client.list_deployments",
            return_value=mock_deployments_ready,
        ),
        patch("httpx.Client") as client_cls,
    ):
        client = MagicMock()
        client_cls.return_value.__enter__.return_value = client
        pause_resp = MagicMock()
        pause_resp.status_code = 200
        pause_resp.content = b"{}"
        client.post.return_value = pause_resp

        result = stop_project("token", target_name="killit", team_id="team_abc")

    assert result["ok"] is True
    assert result["stop_method"] == "project_pause"
    client.post.assert_called_once()
    assert "/v1/projects/prj_test/pause" in client.post.call_args.args[0]
    client.patch.assert_not_called()


def test_stop_cancels_in_flight_build(mock_project, mock_deployments_building):
    with (
        patch(
            "aethos_core.providers.vercel.operations.mutations_api.find_project_by_name",
            return_value=mock_project,
        ),
        patch(
            "aethos_core.providers.vercel.api_client.list_deployments",
            return_value=mock_deployments_building,
        ),
        patch("httpx.Client") as client_cls,
    ):
        client = MagicMock()
        client_cls.return_value.__enter__.return_value = client
        cancel_resp = MagicMock()
        cancel_resp.status_code = 200
        cancel_resp.content = b"{}"
        client.patch.return_value = cancel_resp

        result = stop_project("token", target_name="killit", team_id="team_abc")

    assert result["ok"] is True
    assert result["stop_method"] == "deployment_cancel"
    client.patch.assert_called_once()
    assert client.patch.call_args.args[0].endswith("/v12/deployments/dpl_build/cancel")
    client.post.assert_not_called()
