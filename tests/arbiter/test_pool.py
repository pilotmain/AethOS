# SPDX-License-Identifier: Apache-2.0
"""Pool parsing + validation unit tests."""

import pytest

from aethos_core.arbiter.pool import parse_model_pool, parse_model_pool_string, validate_pool
from aethos_core.config import get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """get_settings() is lru_cached; clear it around each test so monkeypatched
    env vars are actually read by parse_model_pool()."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_parse_valid_pool(monkeypatch):
    monkeypatch.setenv(
        "ARBITER_MODEL_POOL", "anthropic:claude-opus-4-6,openrouter:openai/gpt-4.1-mini"
    )
    get_settings.cache_clear()
    pool = parse_model_pool()
    assert len(pool) == 2
    assert pool[0]["provider"] == "anthropic"
    assert pool[0]["model_id"] == "claude-opus-4-6"
    assert pool[1]["provider"] == "openrouter"
    assert pool[1]["label"] == "GPT-4.1 Mini"


def test_parse_max_cap(monkeypatch):
    entries = ",".join(f"local:llama{i}" for i in range(20))
    monkeypatch.setenv("ARBITER_MODEL_POOL", entries)
    monkeypatch.setenv("ARBITER_MAX_MODELS", "3")
    get_settings.cache_clear()
    pool = parse_model_pool()
    assert len(pool) == 3


def test_parse_skips_unsupported_and_malformed(monkeypatch):
    monkeypatch.setenv(
        "ARBITER_MODEL_POOL",
        "anthropic:claude-opus-4-6,bogusprovider:foo,no-colon-entry,local:llama3.2",
    )
    get_settings.cache_clear()
    pool = parse_model_pool()
    providers = [e["provider"] for e in pool]
    assert providers == ["anthropic", "local"]


def test_parse_dedupes(monkeypatch):
    monkeypatch.setenv(
        "ARBITER_MODEL_POOL", "local:llama3.2,local:llama3.2,anthropic:claude-opus-4-6"
    )
    get_settings.cache_clear()
    pool = parse_model_pool()
    assert len(pool) == 2


def test_parse_empty_string_has_no_explicit_pool():
    # The string parser returns no entries when no explicit pool is set.
    assert parse_model_pool_string("") == []


def test_parse_empty_pool_falls_back_to_connected_models(monkeypatch):
    # §4 — with no explicit ARBITER_MODEL_POOL, the pool defaults to the user's
    # connected models. With none connected (mocked empty), the result is empty.
    monkeypatch.setenv("ARBITER_MODEL_POOL", "")
    monkeypatch.setattr(
        "aethos_core.llm.model_catalog.list_available_models",
        lambda *, include_unconfigured=False: [],
    )
    get_settings.cache_clear()
    assert parse_model_pool() == []


def test_validate_empty_pool():
    result = validate_pool([])
    assert not result["valid"]
    assert "at least 2" in result["errors"][0]


def test_validate_local_only_pool_requires_local_env(monkeypatch):
    monkeypatch.setenv("LOCAL_LLM_ENABLED", "false")
    get_settings.cache_clear()
    pool = [
        {"provider": "local", "model_id": "llama3.2", "label": "Llama 3.2 (local)"},
        {"provider": "local", "model_id": "mistral", "label": "Mistral (local)"},
    ]
    result = validate_pool(pool)
    assert not result["valid"]
    assert any("LOCAL_LLM" in e for e in result["errors"])
