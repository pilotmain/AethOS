# SPDX-License-Identifier: Apache-2.0
"""Generic provider agent ops tests."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.execution_brain.agent_tool_catalog import LEGACY_TOOL_ALIASES, list_model_facing_tool_names
from aethos_core.execution_brain.agent_tool_executor import (
    _normalize_legacy_tool_call,
    execute_agent_tool,
    readonly_agent_tool_schemas,
)
from aethos_core.execution_brain.provider_agent_ops import provider_inventory, provider_inventory_all
from aethos_core.execution_brain.provider_connection_cache import (
    cache_clear_for_tests,
    cache_get,
    cache_invalidate,
    cache_set,
)


def test_provider_read_cache_get_set_and_target_scope():
    cache_clear_for_tests()
    cache_set("railway", {"ok": True, "n": 1}, op="health", target="api")
    cache_set("railway", {"ok": True, "n": 2}, op="health", target="web")
    assert cache_get("railway", op="health", target="api")["n"] == 1
    assert cache_get("railway", op="health", target="web")["n"] == 2
    assert cache_get("railway", op="health", target="other") is None
    cache_clear_for_tests()


def test_provider_read_cache_invalidate_drops_all_ops_for_provider():
    cache_clear_for_tests()
    cache_set("railway", {"ok": True}, op="inventory")
    cache_set("railway", {"ok": True}, op="health", target="api")
    cache_set("vercel", {"ok": True}, op="inventory")
    removed = cache_invalidate("railway")
    assert removed == 2
    assert cache_get("railway", op="inventory") is None
    assert cache_get("railway", op="health", target="api") is None
    assert cache_get("vercel", op="inventory") is not None  # other providers untouched
    cache_clear_for_tests()


def test_provider_inventory_uses_short_ttl_cache():
    cache_clear_for_tests()
    with patch(
        "aethos_core.execution_brain.provider_agent_ops.discover_provider_inventory",
        return_value={"ok": True, "provider": "railway", "inventory": {"resources": []}},
    ) as discover:
        first = provider_inventory("railway")
        second = provider_inventory("railway")
    assert first["ok"] and second["ok"]
    discover.assert_called_once()  # second read served from cache
    cache_invalidate("railway")  # mutation would do this
    with patch(
        "aethos_core.execution_brain.provider_agent_ops.discover_provider_inventory",
        return_value={"ok": True, "provider": "railway", "inventory": {"resources": []}},
    ) as discover2:
        provider_inventory("railway")
    discover2.assert_called_once()  # cache invalidated → re-fetched
    cache_clear_for_tests()


def test_provider_inventory_does_not_cache_failures():
    cache_clear_for_tests()
    with patch(
        "aethos_core.execution_brain.provider_agent_ops.discover_provider_inventory",
        return_value={"ok": False, "error": "token_not_configured"},
    ) as discover:
        provider_inventory("railway")
        provider_inventory("railway")
    assert discover.call_count == 2  # failures are never cached
    cache_clear_for_tests()


def test_model_facing_tools_are_generic_provider_verbs():
    names = set(list_model_facing_tool_names())
    assert "provider_validate" in names
    assert "provider_health" in names
    assert "vercel_list_projects" not in names
    assert "cloud_list_inventory" not in names
    assert len(names) <= 10


def test_legacy_alias_maps_vercel_health_to_provider_health():
    name, inp = _normalize_legacy_tool_call(
        "vercel_deployment_health",
        {"project_name": "aethos", "limit": 2},
    )
    assert name == "provider_health"
    assert inp["provider"] == "vercel"
    assert inp["target_name"] == "aethos"


def test_legacy_tool_names_still_execute():
    assert "railway_fetch_logs" in LEGACY_TOOL_ALIASES
    with patch(
        "aethos_core.execution_brain.provider_agent_ops.provider_logs",
        return_value={"ok": True, "provider": "railway", "logs": []},
    ):
        out = execute_agent_tool("railway_fetch_logs", {"service_name": "aethos-api"})
    assert "railway" in out


def test_provider_inventory_all_quick_skips_discover():
    with patch(
        "aethos_core.execution_brain.provider_agent_ops.list_agent_cloud_providers",
        return_value=["github", "render"],
    ):
        with patch(
            "aethos_core.execution_brain.provider_agent_ops.validate_provider_connection",
            side_effect=lambda p: {"ok": p == "github", "provider": p},
        ):
            with patch(
                "aethos_core.execution_brain.provider_agent_ops.discover_provider_inventory",
            ) as discover:
                payload = provider_inventory_all(limit=2, mode="quick")
                discover.assert_not_called()
    assert payload["mode"] == "quick"
    assert payload["configured_count"] == 1


def test_provider_catalog_tool():
    out = execute_agent_tool("provider_catalog", {})
    assert "provider_validate" in out
