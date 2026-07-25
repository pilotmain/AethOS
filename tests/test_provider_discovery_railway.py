# SPDX-License-Identifier: Apache-2.0
"""Tests for Railway provider discovery."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.config import get_settings
from aethos_core.provider_discovery.inventory_memory import clear_inventory_memory_for_tests, save_inventory_snapshot
from aethos_core.provider_discovery.provider_inventory import (
    ProviderDeploymentRecord,
    ProviderEnvironmentRecord,
    ProviderInventory,
    ProviderProjectRecord,
    ProviderServiceRecord,
)
from aethos_core.providers.railway.discovery import discover_railway_inventory, refresh_railway_inventory


@pytest.fixture(autouse=True)
def _clear_settings():
    get_settings.cache_clear()
    clear_inventory_memory_for_tests()
    yield
    get_settings.cache_clear()
    clear_inventory_memory_for_tests()


def _sample_inventory() -> ProviderInventory:
    services = [
        ProviderServiceRecord(name="api", id="svc-api", type="web", status="online", domain="api.example.app"),
        ProviderServiceRecord(name="worker", id="svc-worker", type="worker", status="online"),
        ProviderServiceRecord(name="redis", id="svc-redis", type="database", status="online"),
        ProviderServiceRecord(name="postgres", id="svc-pg", type="database", status="online"),
    ]
    env = ProviderEnvironmentRecord(name="production", id="env-prod", services=services)
    project = ProviderProjectRecord(name="atlas-trader", id="proj-1", environments=[env])
    return ProviderInventory(
        provider="railway",
        workspace="test@example.com",
        projects=[project],
        last_refreshed_at="2026-01-15T12:00:00+00:00",
        freshness="fresh",
        execution_mode="api",
    )


def test_discovers_api_worker_redis_postgres():
    with patch("aethos_core.providers.railway.discovery._discover_via_api", return_value=_sample_inventory()):
        inventory = discover_railway_inventory()
    names = [row["service_name"] for row in inventory.all_services()]
    assert names == ["api", "worker", "redis", "postgres"]


def test_refresh_persists_inventory_memory():
    inventory = _sample_inventory()
    with patch("aethos_core.providers.railway.discovery.discover_railway_inventory", return_value=inventory):
        refreshed = refresh_railway_inventory(force=True)
    assert refreshed.freshness == "fresh"
    saved = save_inventory_snapshot(refreshed)
    assert saved["ok"] is True


def test_missing_credentials_fails_honestly():
    with patch(
        "aethos_core.providers.railway.discovery.resolve_railway_mutation_credentials",
        return_value=(None, "missing", "Railway credentials missing."),
    ):
        inventory = discover_railway_inventory()
    assert inventory.projects == []
    assert inventory.error
    assert "credential" in inventory.error.lower()


def test_multiple_environments_supported():
    inventory = _sample_inventory()
    staging = ProviderEnvironmentRecord(
        name="staging",
        id="env-staging",
        services=[ProviderServiceRecord(name="api", id="svc-api-staging", status="online")],
    )
    inventory.projects[0].environments.append(staging)
    env_names = [env.name for env in inventory.projects[0].environments]
    assert env_names == ["production", "staging"]
