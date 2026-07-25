# SPDX-License-Identifier: Apache-2.0
"""Provider discovery runtime — load, discover, refresh inventories."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from aethos_core.provider_discovery.inventory_memory import load_inventory_snapshot, save_inventory_snapshot
from aethos_core.provider_discovery.provider_inventory import ProviderInventory
from aethos_core.provider_discovery.provider_refresh import refresh_provider_inventory


def discover_provider_inventory(*, provider: str) -> ProviderInventory:
    provider = (provider or "").strip().lower()
    if provider == "railway":
        from aethos_core.providers.railway.discovery import safe_discover_railway_inventory

        inventory = safe_discover_railway_inventory()
        if inventory.projects:
            save_inventory_snapshot(inventory)
        return inventory
    return ProviderInventory(provider=provider, freshness="unsupported", error=f"No discovery for `{provider}`.")


def get_provider_inventory(*, provider: str, max_age_minutes: int = 30) -> ProviderInventory:
    provider = (provider or "").strip().lower()
    cached = load_inventory_snapshot(provider=provider)
    if cached and cached.last_refreshed_at and _is_fresh(cached.last_refreshed_at, max_age_minutes):
        cached.freshness = "fresh"
        return cached
    if cached and cached.projects:
        cached.freshness = "stale"
        return cached
    return discover_provider_inventory(provider=provider)


def refresh_provider_inventory_runtime(*, provider: str) -> dict[str, Any]:
    return refresh_provider_inventory(provider=provider, force=True)


def _is_fresh(last_refreshed_at: str, max_age_minutes: int) -> bool:
    try:
        ts = datetime.fromisoformat(last_refreshed_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return datetime.now(UTC) - ts <= timedelta(minutes=max_age_minutes)
