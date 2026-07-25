# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from aethos_core.providers.railway.inventory.inventory_adapter import RailwayInventoryAdapter


@patch("aethos_core.providers.railway.api_client.list_services_with_status")
def test_railway_inventory_normalizes_services(mock_list):
    mock_list.return_value = {
        "ok": True,
        "services": [
            {
                "service_id": "svc-1",
                "service_name": "api-worker",
                "project_id": "proj-1",
                "project_name": "backend",
            }
        ],
        "error": None,
    }
    rows = RailwayInventoryAdapter().build_projects_inventory(auth_context={"token": "tok"})
    assert len(rows) == 1
    row = rows[0]
    assert row["provider"] == "railway"
    assert row["name"] == "api-worker"
    assert row["project_id"] == "proj-1"
    assert "source:railway_api" in row["evidence"]


@patch("aethos_core.providers.railway.api_client.list_services_with_status")
def test_railway_inventory_graphql_failure_returns_empty(mock_list):
    mock_list.return_value = {"ok": False, "services": [], "error": "Unauthorized"}
    fetched = RailwayInventoryAdapter().fetch_projects_inventory(auth_context={"token": "tok"})
    assert fetched["ok"] is False
    assert fetched["error"] == "Unauthorized"
    assert RailwayInventoryAdapter().build_projects_inventory(auth_context={"token": "tok"}) == []


def test_railway_inventory_requires_token():
    fetched = RailwayInventoryAdapter().fetch_projects_inventory(auth_context={})
    assert fetched["ok"] is False
    assert RailwayInventoryAdapter().build_projects_inventory(auth_context={}) == []
