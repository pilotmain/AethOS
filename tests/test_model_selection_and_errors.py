# SPDX-License-Identifier: Apache-2.0
"""Per-provider model selection (§1), catalog dedupe (§2), failure classification (§4)."""

from __future__ import annotations

import pytest

from aethos_core import config as config_mod
from aethos_core.runtime_config import runtime_config_store as store


@pytest.fixture(autouse=True)
def _isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_CONFIG_DIR", str(tmp_path / "runtime_config"))
    config_mod.get_settings.cache_clear()
    store.reset_for_tests()
    yield
    store.reset_for_tests()
    config_mod.get_settings.cache_clear()


def _deepseek_spec():
    from aethos_core.llm.model_providers import model_provider_spec

    return model_provider_spec("deepseek")


def test_model_selection_default_all_flagships_enabled():
    from aethos_core.llm.model_selection import enabled_models_for_provider

    spec = _deepseek_spec()
    rows = enabled_models_for_provider(spec)
    ids = [m for m, _ in rows]
    assert "deepseek-chat" in ids and "deepseek-reasoner" in ids


def test_model_selection_disable_and_add_custom():
    from aethos_core.llm.model_selection import (
        enabled_models_for_provider,
        get_provider_model_selection,
        set_provider_model_selection,
    )

    spec = _deepseek_spec()
    # Enable only deepseek-chat (disabling reasoner) and add a custom id.
    set_provider_model_selection(
        "deepseek", enabled_ids=["deepseek-chat", "deepseek-v3-custom"], custom_ids=["deepseek-v3-custom"]
    )
    ids = [m for m, _ in enabled_models_for_provider(spec)]
    assert "deepseek-chat" in ids
    assert "deepseek-reasoner" not in ids
    assert "deepseek-v3-custom" in ids

    sel = get_provider_model_selection("deepseek")
    by_id = {m["model_id"]: m for m in sel["models"]}
    assert by_id["deepseek-reasoner"]["enabled"] is False
    assert by_id["deepseek-v3-custom"]["custom"] is True


def test_unknown_provider_selection_returns_none():
    from aethos_core.llm.model_selection import get_provider_model_selection

    assert get_provider_model_selection("not-a-provider") is None


def test_catalog_dedupe_prefers_configured_direct():
    from aethos_core.llm.model_catalog import DEFAULT_CATALOG_ID, _dedupe_catalog

    rows = [
        {"id": DEFAULT_CATALOG_ID, "provider": "anthropic", "model": "x", "configured": True},
        {"id": "openrouter:openai/gpt-4o", "provider": "openrouter", "model": "openai/gpt-4o", "configured": False},
        {"id": "openai:gpt-4o", "provider": "openai", "model": "gpt-4o", "configured": True},
    ]
    out = _dedupe_catalog(rows)
    ids = [r["id"] for r in out]
    assert ids == [DEFAULT_CATALOG_ID, "openai:gpt-4o"]


def test_catalog_dedupe_keeps_distinct_models():
    from aethos_core.llm.model_catalog import _dedupe_catalog

    rows = [
        {"id": "openai:gpt-4o", "provider": "openai", "model": "gpt-4o", "configured": True},
        {"id": "openai:gpt-4o-mini", "provider": "openai", "model": "gpt-4o-mini", "configured": True},
    ]
    out = _dedupe_catalog(rows)
    assert {r["id"] for r in out} == {"openai:gpt-4o", "openai:gpt-4o-mini"}


@pytest.mark.parametrize(
    "code,category,side",
    [
        (401, "auth", "config"),
        (402, "account_billing", "account"),
        (429, "rate_limited", "account"),
        (503, "unavailable", "transient"),
    ],
)
def test_classify_status(code, category, side):
    from aethos_core.llm.model_error_classifier import classify_status

    verdict = classify_status(code, provider_label="DeepSeek")
    assert verdict["category"] == category
    assert verdict["side"] == side


def test_classify_text_billing_vs_config():
    from aethos_core.llm.model_error_classifier import classify_text

    assert classify_text("HTTP 402 Payment Required")["side"] == "account"
    assert classify_text("Too Many Requests (429)")["category"] == "rate_limited"
    assert classify_text("DeepSeek not configured. Add a key")["side"] == "config"
