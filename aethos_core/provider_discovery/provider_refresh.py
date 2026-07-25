# SPDX-License-Identifier: Apache-2.0
"""Provider inventory refresh orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_discovery.inventory_memory import load_inventory_snapshot, save_inventory_snapshot
from aethos_core.provider_discovery.provider_inventory import ProviderInventory


def refresh_provider_inventory(*, provider: str, force: bool = False) -> dict[str, Any]:
    provider = (provider or "").strip().lower()
    if provider == "railway":
        from aethos_core.providers.railway.discovery import refresh_railway_inventory

        inventory = refresh_railway_inventory(force=force)
        save_inventory_snapshot(inventory)
        return {"ok": not inventory.error, "inventory": inventory.to_dict(), "error": inventory.error}
    return {"ok": False, "error": f"Discovery not implemented for provider `{provider}`."}


def get_cached_provider_inventory(*, provider: str) -> ProviderInventory | None:
    return load_inventory_snapshot(provider=provider)
