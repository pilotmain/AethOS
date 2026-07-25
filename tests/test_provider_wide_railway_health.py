# SPDX-License-Identifier: Apache-2.0
"""Railway provider-wide health report tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.handlers import resolve_handler
from aethos_core.operational_planner.adapters.railway_wide_health import (
    _enrich_health_rows_with_live_deployments,
    collect_railway_service_health_rows,
    compose_railway_provider_wide_health_reply,
)
from aethos_core.operational_planner.planner_router import compose_planned_operational_reply
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests, save_thread_state
from aethos_core.operational_thread_memory.thread_state import OperationalThreadState
from aethos_core.provider_discovery.provider_inventory import (
    ProviderDeploymentRecord,
    ProviderEnvironmentRecord,
    ProviderInventory,
    ProviderProjectRecord,
    ProviderServiceRecord,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_threads_for_tests()
    yield
    clear_threads_for_tests()


def _inventory() -> ProviderInventory:
    return ProviderInventory(
        provider="railway",
        workspace="test@example.com",
        projects=[
            ProviderProjectRecord(
                name="pilotos",
                id="proj-1",
                environments=[
                    ProviderEnvironmentRecord(
                        name="production",
                        id="env-1",
                        services=[
                            ProviderServiceRecord(
                                name="pilotos-api",
                                id="svc-1",
                                type="web",
                                status="online",
                                latest_deployment=ProviderDeploymentRecord(id="dep-1", status="SUCCESS"),
                            )
                        ],
                    )
                ],
            ),
            ProviderProjectRecord(
                name="adequate-luck",
                id="proj-2",
                environments=[
                    ProviderEnvironmentRecord(
                        name="production",
                        id="env-2",
                        services=[
                            ProviderServiceRecord(
                                name="speakglobal-ai",
                                id="svc-2",
                                type="web",
                                status="failed",
                                latest_deployment=ProviderDeploymentRecord(id="dep-2", status="FAILED"),
                            )
                        ],
                    )
                ],
            ),
            ProviderProjectRecord(
                name="atlas-trader",
                id="proj-3",
                environments=[
                    ProviderEnvironmentRecord(
                        name="production",
                        id="env-3",
                        services=[
                            ProviderServiceRecord(
                                name="api",
                                id="svc-3",
                                type="web",
                                status="online",
                                latest_deployment=ProviderDeploymentRecord(id="dep-3", status="SUCCESS"),
                            )
                        ],
                    )
                ],
            ),
        ],
        freshness="fresh",
        execution_mode="api",
    )


def test_enriches_unknown_inventory_rows_with_live_deployments():
    rows = [
        {
            "service": "aethos-api",
            "project": "pilotos",
            "environment": "staging",
            "status": "unknown",
            "health": "unknown",
            "deployment_state": "unknown",
            "service_id": "svc-api",
        }
    ]
    with patch(
        "aethos_core.providers.railway.api_client.list_service_deployments",
        return_value=[{"id": "dep-1", "state": "success", "created_at": "2026-05-29T12:00:00Z"}],
    ), patch(
        "aethos_core.providers.railway.mutations.resolve_railway_mutation_credentials",
        return_value=("token", "settings", None),
    ):
        enriched = _enrich_health_rows_with_live_deployments(rows)
    assert enriched[0]["deployment_state"] == "success"
    assert enriched[0]["status"] == "running"
    assert enriched[0]["health"] == "healthy"


def test_collect_enriches_topology_only_inventory():
    topology_inventory = ProviderInventory(
        provider="railway",
        projects=[
            ProviderProjectRecord(
                name="pilotos",
                id="proj-1",
                environments=[
                    ProviderEnvironmentRecord(
                        name="staging",
                        id="env-1",
                        services=[
                            ProviderServiceRecord(
                                name="aethos-api",
                                id="svc-api",
                                type="web",
                                status="unknown",
                                latest_deployment=None,
                            )
                        ],
                    )
                ],
            )
        ],
        freshness="fresh",
        execution_mode="api",
    )
    with patch(
        "aethos_core.providers.railway.discovery.discover_railway_inventory",
        return_value=topology_inventory,
    ), patch(
        "aethos_core.providers.railway.api_client.list_service_deployments",
        return_value=[{"id": "dep-1", "state": "success"}],
    ), patch(
        "aethos_core.providers.railway.mutations.resolve_railway_mutation_credentials",
        return_value=("token", "settings", None),
    ):
        rows, error = collect_railway_service_health_rows()
    assert error is None
    assert rows[0]["health"] == "healthy"
    assert rows[0]["deployment_state"] == "success"


def test_lists_all_services_with_health_columns():
    with patch(
        "aethos_core.providers.railway.discovery.discover_railway_inventory",
        return_value=_inventory(),
    ):
        rows, error = collect_railway_service_health_rows()
    assert error is None
    assert len(rows) == 3
    names = {row["service"] for row in rows}
    assert names == {"pilotos-api", "speakglobal-ai", "api"}


def test_reports_healthy_running_failed():
    with patch(
        "aethos_core.providers.railway.discovery.discover_railway_inventory",
        return_value=_inventory(),
    ):
        body, intent, meta = compose_railway_provider_wide_health_reply()
    assert intent == "operational_response_conversational"
    assert "Summary:" in body
    assert "Needs attention:" in body
    assert "Full inventory:" in body
    assert "pilotos-api" in body
    assert "speakglobal-ai" in body
    assert "api" in body
    assert "| Service | Project | Environment | Status | Health |" in body
    assert "healthy" in body.lower()
    assert "failed" in body.lower()
    assert meta["service_count"] == "3"


def test_does_not_answer_only_active_thread():
    save_thread_state(
        OperationalThreadState(
            session_id="wide-health",
            provider="railway",
            project="pilotos",
            environment="production",
            service="pilotos-api",
            operation="restart",
            status="stabilizing",
        )
    )
    text = (
        "check all the services available in railway and report back with "
        "running - healthy and failed with the service names"
    )
    with patch(
        "aethos_core.providers.railway.discovery.discover_railway_inventory",
        return_value=_inventory(),
    ):
        reply, intent, meta = compose_planned_operational_reply(text, session_id="wide-health")
    assert reply is not None
    assert "not just the active operational thread" in reply or "provider-wide" in reply.lower()
    assert "speakglobal-ai" in reply
    assert "pilotos-api" in reply
    assert meta["scope"] == "provider_wide"


def test_resolve_handler_routes_provider_wide_before_followup():
    save_thread_state(
        OperationalThreadState(
            session_id="handler-wide",
            provider="railway",
            service="pilotos-api",
            operation="restart",
            status="stabilizing",
        )
    )
    text = "check all services in railway and report healthy vs failed"
    with patch(
        "aethos_core.providers.railway.discovery.discover_railway_inventory",
        return_value=_inventory(),
    ):
        packed = resolve_handler(text, session_id="handler-wide")
    assert packed is not None
    reply, intent, meta = packed
    assert intent == "operational_response_conversational"
    assert "pilotos-api" in reply
    assert "speakglobal-ai" in reply
    assert meta.get("scope") == "provider_wide"
