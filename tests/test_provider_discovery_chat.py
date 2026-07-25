# SPDX-License-Identifier: Apache-2.0
"""Provider discovery chat tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.config import get_settings
from aethos_core.provider_discovery.inventory_memory import clear_inventory_memory_for_tests, save_inventory_snapshot
from aethos_core.provider_discovery.provider_inventory import (
    ProviderEnvironmentRecord,
    ProviderInventory,
    ProviderProjectRecord,
    ProviderServiceRecord,
)


@pytest.fixture(autouse=True)
def _clear_settings():
    get_settings.cache_clear()
    clear_inventory_memory_for_tests()
    yield
    get_settings.cache_clear()
    clear_inventory_memory_for_tests()


@pytest.fixture(autouse=True)
def _inventory_only_when_seeded():
    from aethos_core.provider_discovery.discovery_runtime import load_inventory_snapshot
    from aethos_core.provider_discovery.provider_inventory import ProviderInventory
    from unittest.mock import patch

    def _inventory(provider: str, max_age_minutes: int = 30):
        _ = max_age_minutes
        cached = load_inventory_snapshot(provider=provider)
        if cached and cached.projects:
            cached.freshness = "fresh"
            return cached
        return ProviderInventory(provider=provider, projects=[], freshness="unavailable")

    with patch("aethos_core.provider_discovery.discovery_runtime.get_provider_inventory", side_effect=_inventory):
        with patch("aethos_core.provider_discovery.discovery_runtime.discover_provider_inventory", side_effect=_inventory):
            yield


def _seed_inventory() -> None:
    services = [
        ProviderServiceRecord(name="api", id="svc-api", status="online", domain="api.example.app"),
        ProviderServiceRecord(name="worker", id="svc-worker", status="online"),
        ProviderServiceRecord(name="redis", id="svc-redis", status="online"),
        ProviderServiceRecord(name="postgres", id="svc-pg", status="online"),
    ]
    env = ProviderEnvironmentRecord(name="production", id="env-prod", services=services)
    project = ProviderProjectRecord(name="atlas-trader", id="proj-1", environments=[env])
    inventory = ProviderInventory(provider="railway", projects=[project], freshness="fresh")
    save_inventory_snapshot(inventory)


def test_what_railway_services_intent():
    from aethos_core.api.main import app

    _seed_inventory()
    client = TestClient(app)
    response = client.post("/api/v1/chat", json={"message": "What Railway services do I have?", "session_id": "disc"})
    body = response.json()
    assert body.get("intent") == "provider_discovery_inventory"
    reply = body["reply"].lower()
    for name in ("api", "worker", "redis", "postgres"):
        assert name in reply


def test_restart_worker_creates_preflight(monkeypatch):
    from aethos_core.api.main import app

    _seed_inventory()
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    get_settings.cache_clear()
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={"message": "Restart the Railway worker service", "session_id": "disc-worker"},
    )
    body = response.json()
    assert body.get("intent") in {"mutation_preflight_job_created", "mutation_target_clarification"}
    if body.get("intent") == "mutation_preflight_job_created":
        assert "worker" in body["reply"].lower()
        assert "preflight" in body["reply"].lower() or "governed" in body["reply"].lower()


def test_restart_railway_ambiguous_no_preflight():
    from aethos_core.api.main import app

    _seed_inventory()
    client = TestClient(app)
    response = client.post("/api/v1/chat", json={"message": "Restart Railway", "session_id": "disc-ambig"})
    body = response.json()
    assert body.get("intent") == "mutation_target_clarification"
    assert "preflight" in body["reply"].lower() or "which" in body["reply"].lower()


def test_why_is_api_failing():
    from aethos_core.api.main import app

    _seed_inventory()
    client = TestClient(app)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "aethos_core.providers.railway.cli_executor.railway_logs",
            lambda **kwargs: {
                "ok": True,
                "logs": [{"message": "DATABASE_URL is missing", "timestamp": "2026-01-15T12:00:00+00:00"}],
            },
        )
        response = client.post(
            "/api/v1/chat",
            json={"message": "Why is api failing?", "session_id": "disc-fail"},
        )
    body = response.json()
    assert body.get("intent") == "provider_discovery_diagnosis"
    assert "database" in body["reply"].lower() or "config" in body["reply"].lower()
