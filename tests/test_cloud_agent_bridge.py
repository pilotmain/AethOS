# SPDX-License-Identifier: Apache-2.0
"""Global Mission Control cloud agent bridge tests."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool
from aethos_core.execution_brain.cloud_agent_bridge import (
    discover_provider_inventory,
    list_all_provider_inventory,
    validate_provider_connection,
)
from aethos_core.execution_brain.cloud_provider_catalog import (
    is_registered_provider,
    list_agent_cloud_providers,
)


def test_mission_control_lists_many_providers():
    names = list_agent_cloud_providers()
    assert "vercel" in names
    assert "railway" in names
    assert "github" in names
    assert "render" in names
    assert is_registered_provider("supabase")


def test_provider_catalog_tool_legacy_alias():
    out = execute_agent_tool("cloud_list_providers", {})
    assert "vercel" in out
    assert "render" in out


def test_validate_unknown_provider():
    payload = validate_provider_connection("not-a-real-provider")
    assert payload["ok"] is False
    assert payload["error"] == "unknown_provider"


def test_discover_render_uses_vault_token_and_fetcher():
    fake_validation = {"ok": True, "detail": "Render token ok"}
    fake_list = {"ok": True, "resource_count": 1, "resources": [{"name": "api", "status": "live"}]}
    with patch(
        "aethos_core.execution_brain.cloud_agent_bridge.resolve_provider_token",
        return_value=("render-test-token", None),
    ):
        with patch(
            "aethos_core.providers.cloud.validators.validate_cloud_provider_token",
            return_value=fake_validation,
        ):
            with patch(
                "aethos_core.execution_brain.provider_inventory_registry.fetch_provider_inventory",
                return_value=fake_list,
            ):
                payload = discover_provider_inventory("render")
    assert payload["ok"] is True
    assert payload["inventory"]["resource_count"] == 1


def test_cloud_validate_connection_legacy_alias():
    with patch(
        "aethos_core.execution_brain.provider_agent_ops.provider_validate",
        return_value={"ok": True, "provider": "github", "detail": "ok"},
    ):
        out = execute_agent_tool("cloud_validate_connection", {"provider": "github"})
    assert "github" in out
    assert "ok" in out


def test_list_all_inventory_delegates_to_provider_ops():
    with patch(
        "aethos_core.execution_brain.provider_agent_ops.provider_inventory_all",
        return_value={"ok": True, "provider_count": 3, "configured_count": 1, "mode": "full"},
    ) as scan:
        payload = list_all_provider_inventory(limit=5, mode="full")
        scan.assert_called_once()
    assert payload["configured_count"] == 1
