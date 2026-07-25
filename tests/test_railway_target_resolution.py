# SPDX-License-Identifier: Apache-2.0
"""Railway target resolution — aliases, inventory, and API matching."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.config import get_settings
from aethos_core.provider_discovery.inventory_memory import clear_inventory_memory_for_tests
from aethos_core.providers.railway.target_resolver import (
    TARGET_APPROVAL_THRESHOLD,
    ProviderTarget,
    extract_railway_service_phrase,
    resolve_railway_provider_target,
)


@pytest.fixture(autouse=True)
def _clear_inventory():
    get_settings.cache_clear()
    clear_inventory_memory_for_tests()
    yield
    clear_inventory_memory_for_tests()
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _no_live_provider_discovery():
    from aethos_core.provider_discovery.discovery_runtime import load_inventory_snapshot
    from aethos_core.provider_discovery.provider_inventory import ProviderInventory

    def _inventory(provider: str, max_age_minutes: int = 30):
        _ = max_age_minutes
        cached = load_inventory_snapshot(provider=provider)
        if cached and cached.projects:
            cached.freshness = "fresh"
            return cached
        return ProviderInventory(provider=provider, projects=[], freshness="unavailable")

    with patch("aethos_core.provider_discovery.discovery_runtime.get_provider_inventory", side_effect=_inventory):
        yield


def test_extract_railway_service_phrase_multi_word():
    phrase = extract_railway_service_phrase("Restart the Railway atlas-trader api service")
    assert phrase == "atlas-trader api"


def test_resolves_atlas_trader_api_alias():
    target = resolve_railway_provider_target(
        user_request="Restart the Railway atlas-trader api service",
        operation_type="restart",
    )
    assert target.resolved is True
    assert target.service_name == "atlas-trader api"
    assert target.project_name == "atlas-trader"
    assert target.environment == "production"
    assert target.confidence >= TARGET_APPROVAL_THRESHOLD
    assert target.source == "alias_map"


def test_resolves_alias_variant_atlas_trader_api():
    target = resolve_railway_provider_target(
        user_request="Railway atlas trader api restart",
        operation_type="restart",
    )
    assert target.resolved is True
    assert target.service_name == "atlas-trader api"


def test_ambiguous_target_returns_candidates():
    inventory = [
        {"service_name": "atlas-trader api", "project_name": "atlas-trader"},
        {"service_name": "atlas-trader web", "project_name": "atlas-trader"},
    ]

    with patch(
        "aethos_core.providers.railway.target_resolver.list_railway_inventory_services",
        return_value=inventory,
    ):
        target = resolve_railway_provider_target(user_request="Restart Railway", operation_type="restart")

    assert target.resolved is False
    assert target.reason == "missing_target_phrase"
    assert len(target.candidates) >= 2


def test_unknown_target_blocks_resolution():
    with patch(
        "aethos_core.providers.railway.target_resolver._api_match",
        return_value=ProviderTarget(
            provider="railway",
            service_name="unknown-service",
            confidence=0.0,
            resolved=False,
            reason="service_not_found",
            candidates=[],
            source="provider_api",
        ),
    ):
        with patch("aethos_core.providers.railway.target_resolver._alias_match", return_value=None):
            with patch("aethos_core.providers.railway.target_resolver._inventory_match", return_value=None):
                target = resolve_railway_provider_target(
                    user_request="Restart Railway unknown-service",
                    operation_type="restart",
                )
    assert target.resolved is False
    assert target.reason == "service_not_found"


def test_inventory_unavailable_asks_clarification():
    with patch(
        "aethos_core.providers.railway.target_resolver.list_railway_inventory_services",
        return_value=[],
    ):
        with patch(
            "aethos_core.providers.railway.target_resolver._api_match",
            return_value=ProviderTarget(
                provider="railway",
                confidence=0.0,
                resolved=False,
                reason="provider_inventory_unavailable",
                source="provider_api",
            ),
        ):
            target = resolve_railway_provider_target(user_request="Restart Railway", operation_type="restart")
    assert target.resolved is False
    assert target.reason == "provider_inventory_unavailable"
