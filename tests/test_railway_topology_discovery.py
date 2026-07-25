# SPDX-License-Identifier: Apache-2.0
"""Railway topology discovery + selection preflight tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from aethos_core.config import get_settings
from aethos_core.provider_discovery.provider_inventory import (
    ProviderEnvironmentRecord,
    ProviderInventory,
    ProviderProjectRecord,
    ProviderServiceRecord,
)
from aethos_core.provider_discovery.target_resolution import resolve_target_from_inventory
from aethos_core.task_frame.task_memory import clear_task_frames_for_tests


def _inventory() -> ProviderInventory:
    services = [
        ProviderServiceRecord(name="api", id="svc-api"),
        ProviderServiceRecord(name="worker", id="svc-worker"),
        ProviderServiceRecord(name="redis", id="svc-redis"),
        ProviderServiceRecord(name="postgres", id="svc-pg"),
    ]
    env = ProviderEnvironmentRecord(name="production", id="env-prod", services=services)
    project = ProviderProjectRecord(name="atlas-trader", id="proj-1", environments=[env])
    crm_services = [
        ProviderServiceRecord(name="influencer-crm", id="svc-crm"),
        ProviderServiceRecord(name="api", id="svc-crm-api"),
    ]
    crm_env = ProviderEnvironmentRecord(name="production", id="env-crm", services=crm_services)
    crm_project = ProviderProjectRecord(name="influencer-crm", id="proj-crm", environments=[crm_env])
    demo_services = [ProviderServiceRecord(name="api", id="svc-demo-api")]
    demo_env = ProviderEnvironmentRecord(name="production", id="env-demo", services=demo_services)
    demo_project = ProviderProjectRecord(name="demo-app", id="proj-demo", environments=[demo_env])
    return ProviderInventory(provider="railway", projects=[project, crm_project, demo_project], freshness="fresh")


@pytest.fixture(autouse=True)
def _clean():
    get_settings.cache_clear()
    clear_task_frames_for_tests()
    yield
    clear_task_frames_for_tests()
    get_settings.cache_clear()


def test_lists_all_services():
    names = [row["service_name"] for row in _inventory().all_services()]
    assert "api" in names
    assert "worker" in names
    assert "redis" in names
    assert "postgres" in names
    assert "influencer-crm" in names


def test_resolves_api_under_correct_project():
    resolution = resolve_target_from_inventory(
        inventory=_inventory(),
        user_request="Restart atlas-trader api",
        target_hints=["atlas-trader api"],
    )
    assert resolution.resolved is True
    assert resolution.project_name == "atlas-trader"
    assert resolution.service_name == "api"


def test_resolves_influencer_crm_service():
    resolution = resolve_target_from_inventory(
        inventory=_inventory(),
        user_request="Restart influencer-crm / production / influencer-crm",
    )
    assert resolution.resolved is True
    assert resolution.project_name == "influencer-crm"
    assert resolution.service_name == "influencer-crm"


def test_ambiguous_api_asks_clarification():
    resolution = resolve_target_from_inventory(
        inventory=_inventory(),
        user_request="Restart Railway api",
    )
    assert resolution.resolved is False
    assert resolution.reason == "ambiguous_inventory_match"


def test_selected_candidate_creates_preflight_via_task_frame(monkeypatch):
    from aethos_core.api.main import app
    from aethos_core.task_frame.clarification_state import store_target_selection_task

    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    get_settings.cache_clear()
    inventory = _inventory()
    candidates = inventory.all_services()
    api_candidates = [row for row in candidates if row["service_name"] == "api"]
    store_target_selection_task(
        session_id="topo-preflight",
        provider="railway",
        operation="restart",
        original_request="Restart Railway api",
        candidates=api_candidates,
    )
    client = TestClient(app)
    response = client.post("/api/v1/chat", json={"message": "1", "session_id": "topo-preflight"})
    body = response.json()
    assert body.get("intent") == "task_frame_preflight_created"
