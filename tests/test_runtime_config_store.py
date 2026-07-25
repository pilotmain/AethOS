# SPDX-License-Identifier: Apache-2.0
"""Runtime configuration store + resolver + guardrails, and arbiter pool defaulting.

Covers §1 (UI-writable store, precedence store->env->default), §3 (secrets/dangerous
keys rejected, allowlist enforced), and §4 (arbiter pool from connected models).
"""

from __future__ import annotations

import pytest

from aethos_core import config as config_mod
from aethos_core.runtime_config import runtime_config_store as store
from aethos_core.runtime_config.effective_settings import (
    ConfigWriteError,
    effective_bool,
    effective_setting,
    list_effective_settings,
    revert_effective_setting,
    set_effective_setting,
)


@pytest.fixture(autouse=True)
def _isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_CONFIG_DIR", str(tmp_path / "runtime_config"))
    config_mod.get_settings.cache_clear()
    store.reset_for_tests()
    yield
    store.reset_for_tests()
    config_mod.get_settings.cache_clear()


def test_store_set_get_delete_roundtrip():
    assert store.get_runtime_value("X") is None
    store.set_runtime_value("X", "1")
    assert store.get_runtime_value("X") == "1"
    assert store.delete_runtime_value("X") is True
    assert store.get_runtime_value("X") is None


def test_effective_setting_precedence_store_over_env_default(monkeypatch):
    # Default (.env unset) is True for arbiter when batteries included.
    monkeypatch.setenv("AETHOS_BATTERIES_INCLUDED", "true")
    config_mod.get_settings.cache_clear()
    assert effective_bool("ARBITER_ENABLED") is True
    res = set_effective_setting("ARBITER_ENABLED", False)
    assert res["source"] == "runtime_store"
    assert effective_bool("ARBITER_ENABLED") is False
    # Live settings singleton honors the override (no call-site changes).
    assert config_mod.get_settings().arbiter_enabled is False
    # Revert falls back to the .env/default value.
    revert_effective_setting("ARBITER_ENABLED")
    assert effective_bool("ARBITER_ENABLED") is True


def test_override_survives_settings_rebuild():
    set_effective_setting("ARBITER_ENABLED", True)
    config_mod.get_settings.cache_clear()  # simulate a fresh process / boot
    assert config_mod.get_settings().arbiter_enabled is True


def test_secret_keys_rejected():
    with pytest.raises(ConfigWriteError) as exc:
        set_effective_setting("ANTHROPIC_API_KEY", "sk-test")
    assert exc.value.code == "secret_not_allowed"


def test_dangerous_flags_rejected():
    for key in (
        "AETHOS_SOLO_EXECUTION_MODE",
        "AUTONOMOUS_EXECUTION_ENABLED",
        "MUTATION_T3_PRODUCTION_ENABLED",
    ):
        with pytest.raises(ConfigWriteError) as exc:
            set_effective_setting(key, True)
        assert exc.value.code == "operator_only"


def test_unknown_key_rejected():
    with pytest.raises(ConfigWriteError) as exc:
        set_effective_setting("TOTALLY_MADE_UP_FLAG", "x")
    assert exc.value.code == "unknown_key"


def test_enum_validation():
    with pytest.raises(ConfigWriteError) as exc:
        set_effective_setting("WEB_SEARCH_PROVIDER", "not-a-provider")
    assert exc.value.code == "invalid_value"
    set_effective_setting("WEB_SEARCH_PROVIDER", "tavily")
    assert effective_setting("WEB_SEARCH_PROVIDER") == "tavily"


def test_list_effective_settings_grouped():
    payload = list_effective_settings()
    groups = {g["group"] for g in payload["groups"]}
    assert {"Features", "Models", "Channels", "Services"} <= groups
    keys = {s["key"] for g in payload["groups"] for s in g["settings"]}
    assert "ARBITER_ENABLED" in keys
    assert "ARBITER_MODEL_POOL" in keys
    # No secret/dangerous key ever appears in the user-facing list.
    assert not any("API_KEY" in k or k == "MUTATION_EXECUTION_ENABLED" for k in keys)


def test_arbiter_pool_defaults_to_connected_models(monkeypatch):
    from aethos_core.arbiter import pool as pool_mod

    fake_models = [
        {"id": "default", "provider": "anthropic", "model": "claude-x", "label": "Default"},
        {"id": "anthropic:claude-sonnet-4-6", "provider": "anthropic", "model": "claude-sonnet-4-6", "label": "Claude Sonnet 4.6"},
        {"id": "deepseek:deepseek-chat", "provider": "deepseek", "model": "deepseek-chat", "label": "DeepSeek · Chat"},
    ]
    monkeypatch.setattr(
        "aethos_core.llm.model_catalog.list_available_models",
        lambda *, include_unconfigured=False: fake_models,
    )
    # No explicit pool set -> should fall back to connected models (skipping "default").
    pool = pool_mod.parse_model_pool()
    providers = {e["provider"] for e in pool}
    assert providers == {"anthropic", "deepseek"}
    assert len(pool) == 2


def test_arbiter_explicit_ui_pool_takes_precedence():
    # A UI-selected pool persists via the runtime store and wins over the default.
    set_effective_setting("ARBITER_MODEL_POOL", "anthropic:claude-sonnet-4-6,openrouter:openai/gpt-4.1-mini")
    from aethos_core.arbiter import pool as pool_mod

    pool = pool_mod.parse_model_pool()
    assert {e["provider"] for e in pool} == {"anthropic", "openrouter"}


def test_validate_pool_flags_missing_registry_key(monkeypatch):
    from aethos_core.arbiter import pool as pool_mod

    monkeypatch.setattr(
        "aethos_core.llm.model_providers.resolve_model_provider_key",
        lambda provider: "",
    )
    result = pool_mod.validate_pool(
        [
            {"provider": "deepseek", "model_id": "deepseek-chat", "label": "DeepSeek"},
            {"provider": "openai", "model_id": "gpt-4o", "label": "GPT-4o"},
        ]
    )
    assert result["valid"] is False
    assert any("deepseek" in e for e in result["errors"])
