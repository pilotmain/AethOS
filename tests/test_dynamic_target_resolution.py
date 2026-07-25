# SPDX-License-Identifier: Apache-2.0
"""Dynamic target resolution from provider inventory."""

from __future__ import annotations

from aethos_core.provider_discovery.provider_inventory import (
    ProviderEnvironmentRecord,
    ProviderInventory,
    ProviderProjectRecord,
    ProviderServiceRecord,
)
from aethos_core.provider_discovery.target_resolution import (
    TARGET_APPROVAL_THRESHOLD,
    resolve_target_from_inventory,
)


def _inventory() -> ProviderInventory:
    services = [
        ProviderServiceRecord(name="api", id="svc-api", aliases=["atlas-trader api"]),
        ProviderServiceRecord(name="worker", id="svc-worker"),
        ProviderServiceRecord(name="web", id="svc-web"),
    ]
    env = ProviderEnvironmentRecord(name="production", id="env-prod", services=services)
    project = ProviderProjectRecord(name="atlas-trader", id="proj-1", environments=[env])
    return ProviderInventory(provider="railway", projects=[project], freshness="fresh")


def test_resolves_api():
    resolution = resolve_target_from_inventory(
        inventory=_inventory(),
        user_request="Restart the api",
    )
    assert resolution.resolved is True
    assert resolution.service_name == "api"
    assert resolution.confidence >= TARGET_APPROVAL_THRESHOLD


def test_resolves_worker():
    resolution = resolve_target_from_inventory(
        inventory=_inventory(),
        user_request="Restart the Railway worker service",
    )
    assert resolution.resolved is True
    assert resolution.service_name == "worker"


def test_resolves_atlas_trader_api_alias():
    resolution = resolve_target_from_inventory(
        inventory=_inventory(),
        user_request="Restart atlas-trader api",
    )
    assert resolution.resolved is True
    assert resolution.service_name == "api"


def test_ambiguous_service_asks_clarification():
    inventory = _inventory()
    demo_env = ProviderEnvironmentRecord(
        name="production",
        id="env-demo",
        services=[ProviderServiceRecord(name="api", id="svc-demo-api")],
    )
    inventory.projects.append(ProviderProjectRecord(name="demo-app", id="proj-2", environments=[demo_env]))
    resolution = resolve_target_from_inventory(
        inventory=inventory,
        user_request="Restart Railway api",
    )
    assert resolution.resolved is False
    assert resolution.reason == "ambiguous_inventory_match"
    assert len(resolution.candidates) >= 2


def test_no_target_no_preflight_reason():
    resolution = resolve_target_from_inventory(
        inventory=_inventory(),
        user_request="Restart Railway",
    )
    assert resolution.resolved is False
    assert resolution.reason == "missing_target_phrase"


def test_no_inventory_unavailable():
    resolution = resolve_target_from_inventory(
        inventory=ProviderInventory(provider="railway", projects=[]),
        user_request="Restart worker",
    )
    assert resolution.resolved is False
    assert resolution.reason == "provider_inventory_unavailable"
