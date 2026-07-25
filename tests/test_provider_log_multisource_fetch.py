# SPDX-License-Identifier: Apache-2.0
"""Railway multi-source log fetch tests."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.providers.railway.operations.logs_multisource import fetch_railway_logs_multisource


def test_runtime_logs_available():
    with patch(
        "aethos_core.providers.railway.mutations.resolve_railway_mutation_credentials",
        return_value=("token", "env", None),
    ), patch(
        "aethos_core.providers.railway.api_client.find_service_by_name",
        return_value={"service_id": "svc-1", "service_name": "pilotos-api"},
    ), patch(
        "aethos_core.providers.railway.api_client.list_service_deployments",
        return_value=[{"id": "dep-1", "state": "SUCCESS"}],
    ), patch(
        "aethos_core.providers.railway.api_client.fetch_deployment_logs",
        return_value=[{"timestamp": "2026-05-20T12:00:00+00:00", "level": "INFO", "message": "runtime boot"}],
    ), patch(
        "aethos_core.providers.railway.cli_executor.railway_logs",
        return_value={"logs": []},
    ):
        payload = fetch_railway_logs_multisource(service_name="pilotos-api", limit=5)
    assert payload["ok"] is True
    assert payload["logs"][0]["message"] == "runtime boot"
    assert "runtime_logs_after" in payload["sources_checked"]


def test_build_logs_via_deployment_scan():
    with patch(
        "aethos_core.providers.railway.mutations.resolve_railway_mutation_credentials",
        return_value=("token", "env", None),
    ), patch(
        "aethos_core.providers.railway.api_client.find_service_by_name",
        return_value={"service_id": "svc-1", "service_name": "pilotos-api"},
    ), patch(
        "aethos_core.providers.railway.api_client.list_service_deployments",
        return_value=[{"id": "dep-1", "state": "BUILDING"}, {"id": "dep-2", "state": "SUCCESS"}],
    ), patch(
        "aethos_core.providers.railway.api_client.fetch_deployment_logs",
        side_effect=[
            [{"timestamp": "2026-05-20T11:00:00+00:00", "level": "INFO", "message": "build step"}],
            [{"timestamp": "2026-05-20T12:00:00+00:00", "level": "INFO", "message": "runtime ready"}],
        ],
    ), patch(
        "aethos_core.providers.railway.cli_executor.railway_logs",
        return_value={"logs": []},
    ):
        payload = fetch_railway_logs_multisource(service_name="pilotos-api", limit=5)
    assert payload["ok"] is True
    assert any("build" in row.get("message", "") or "runtime" in row.get("message", "") for row in payload["logs"])


def test_cli_runtime_logs_used_when_api_empty():
    with patch(
        "aethos_core.providers.railway.mutations.resolve_railway_mutation_credentials",
        return_value=(None, None, "missing token"),
    ), patch(
        "aethos_core.providers.railway.cli_executor.railway_logs",
        return_value={"logs": [{"timestamp": "2026-05-20T12:05:00+00:00", "message": "cli runtime line"}]},
    ):
        payload = fetch_railway_logs_multisource(service_name="pilotos-api", limit=3)
    assert payload["ok"] is True
    assert "runtime_logs_after" in payload["sources_checked"]
    assert payload["logs"][0]["message"] == "cli runtime line"


def test_all_sources_fail_returns_bounded_uncertainty():
    with patch(
        "aethos_core.providers.railway.mutations.resolve_railway_mutation_credentials",
        return_value=(None, None, "missing token"),
    ), patch(
        "aethos_core.providers.railway.cli_executor.railway_logs",
        return_value={"logs": []},
    ):
        payload = fetch_railway_logs_multisource(service_name="pilotos-api", limit=5)
    assert payload["ok"] is False
    assert payload["all_sources_failed"] is True
