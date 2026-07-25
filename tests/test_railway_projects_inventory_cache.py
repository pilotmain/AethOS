# SPDX-License-Identifier: Apache-2.0
"""Railway projects inventory chat helpers."""

from __future__ import annotations

from aethos_core.provider_discovery.provider_inventory import (
    ProviderEnvironmentRecord,
    ProviderInventory,
    ProviderProjectRecord,
    ProviderServiceRecord,
)
from aethos_core.provider_discovery.inventory_memory import clear_inventory_memory_for_tests, save_inventory_snapshot
from aethos_core.providers.railway.inventory.railway_projects_chat import (
    build_railway_inventory_summary_from_cache,
    should_use_cached_railway_inventory,
)


def test_should_use_cached_railway_inventory_on_rate_limit() -> None:
    assert should_use_cached_railway_inventory(error="Rate limit exceeded, please try again in 600 seconds.")
    assert not should_use_cached_railway_inventory(error="invalid token")


def test_build_railway_inventory_summary_from_cache() -> None:
    clear_inventory_memory_for_tests()
    save_inventory_snapshot(
        ProviderInventory(
            provider="railway",
            projects=[
                ProviderProjectRecord(
                    name="pilotos",
                    id="p1",
                    environments=[
                        ProviderEnvironmentRecord(
                            name="production",
                            id="e1",
                            services=[ProviderServiceRecord(name="aethos-api", id="s1")],
                        )
                    ],
                )
            ],
            last_refreshed_at="2026-06-01T00:00:00+00:00",
            freshness="stale",
        )
    )
    summary = build_railway_inventory_summary_from_cache()
    assert summary is not None
    assert summary["ok"] is True
    assert summary["stale_cache"] is True
    assert summary["project_count"] == 1
    assert summary["service_count"] == 1
