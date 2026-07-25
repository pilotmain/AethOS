# SPDX-License-Identifier: Apache-2.0
"""Agent runtime speed shortcuts — deterministic paths and connection cache."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.config import get_settings
from aethos_core.execution_brain.agent_deterministic_shortcuts import (
    match_agent_deterministic_shortcut,
    run_agent_deterministic_shortcut,
)
from aethos_core.execution_brain.agent_runtime import run_agent_runtime_turn
from aethos_core.execution_brain.provider_connection_cache import cache_clear_for_tests, cache_get, cache_set
from aethos_core.provider.completion import _truncate_tool_result


def test_match_catalog_shortcut():
    assert (
        match_agent_deterministic_shortcut(
            "List all providers in Mission Control Provider Inventory and tell me which ones support health checks vs validate-only"
        )
        == "provider_catalog"
    )


def test_match_quick_scan_shortcut():
    assert match_agent_deterministic_shortcut("Run a quick scan of all configured cloud providers") == "provider_inventory_all_quick"


def test_deterministic_catalog_skips_llm(monkeypatch):
    monkeypatch.setattr(get_settings(), "agent_runtime_enabled", True)
    monkeypatch.setattr(get_settings(), "use_real_llm", True)
    monkeypatch.setattr(get_settings(), "anthropic_api_key", "sk-test")
    fake_payload = '{"ok": true, "provider_count": 1, "providers": [{"label": "Vercel", "provider": "vercel", "capabilities": ["validate", "health"]}]}'
    with patch("aethos_core.execution_brain.agent_tool_executor.execute_agent_tool", return_value=fake_payload):
        out = run_agent_deterministic_shortcut(
            "List all providers in Mission Control Provider Inventory",
            session_id="shortcut-test",
        )
    assert out is not None
    assert "Health checks supported" in out["reply"]
    assert "Vercel" in out["reply"]
    assert out["meta"]["shortcut"] == "provider_catalog"


def test_agent_runtime_uses_deterministic_shortcut(monkeypatch):
    monkeypatch.setattr(get_settings(), "agent_runtime_enabled", True)
    monkeypatch.setattr(get_settings(), "use_real_llm", True)
    monkeypatch.setattr(get_settings(), "anthropic_api_key", "sk-test")
    with patch(
        "aethos_core.execution_brain.agent_deterministic_shortcuts.run_agent_deterministic_shortcut",
        return_value={"reply": "catalog", "meta": {"route_id": "agent_deterministic_catalog"}},
    ), patch("aethos_core.provider.completion.run_anthropic_tool_loop") as mock_loop:
        result = run_agent_runtime_turn(
            "List all providers in Mission Control Provider Inventory",
            session_id="shortcut-runtime",
        )
    mock_loop.assert_not_called()
    assert result is not None
    assert result.used_llm is False
    assert result.reply == "catalog"


def test_connection_cache_round_trip():
    cache_clear_for_tests()
    cache_set("vercel", {"ok": True, "provider": "vercel"}, op="validate", ttl_sec=60.0)
    hit = cache_get("vercel", op="validate")
    assert hit is not None
    assert hit["ok"] is True
    cache_clear_for_tests()


def test_truncate_tool_result():
    long_text = "x" * 20_000
    trimmed = _truncate_tool_result(long_text, max_chars=100)
    assert len(trimmed) <= 100
    assert "truncated" in trimmed
