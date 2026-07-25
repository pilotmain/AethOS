# SPDX-License-Identifier: Apache-2.0
"""Anthropic as first-class MODEL_PROVIDERS registry entry."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings


@pytest.fixture(autouse=True)
def _clear_settings():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_anthropic_in_model_providers_registry():
    from aethos_core.llm.model_providers import MODEL_PROVIDERS, model_provider_spec

    assert "anthropic" in MODEL_PROVIDERS
    spec = model_provider_spec("anthropic")
    assert spec is not None
    assert spec.openai_compatible is False
    assert len(spec.models) >= 3


def test_anthropic_key_from_vault_not_env_for_non_default_tenant(monkeypatch):
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env-should-not-use")
    get_settings.cache_clear()

    from aethos_core.security.credential_vault import get_credential_vault, reset_credential_vault_for_tests
    from aethos_core.tenancy import tenant_scope

    reset_credential_vault_for_tests()
    vault = get_credential_vault()
    vault.clear_all_for_tests()
    try:
        with tenant_scope("tenant-jeremy"):
            rec = vault.store_api_token(
            provider="anthropic",
            label="Jeremy Anthropic",
            token="sk-ant-jeremy-vault-key-1234567890",
        )
        assert rec.credential_id
        with tenant_scope("tenant-jeremy"):
            from aethos_core.llm.model_providers import resolve_model_provider_key

            assert resolve_model_provider_key("anthropic") == "sk-ant-jeremy-vault-key-1234567890"
    finally:
        reset_credential_vault_for_tests()
        vault.clear_all_for_tests()
        get_settings.cache_clear()


def test_anthropic_catalog_when_vault_key_only(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("USE_REAL_LLM", "true")
    get_settings.cache_clear()

    from aethos_core.security.credential_vault import get_credential_vault, reset_credential_vault_for_tests

    reset_credential_vault_for_tests()
    vault = get_credential_vault()
    vault.clear_all_for_tests()
    vault.store_api_token(
        provider="anthropic",
        label="Vault Anthropic",
        token="sk-ant-vault-only-key-1234567890",
    )
    from aethos_core.llm.model_catalog import list_available_models

    rows = [r for r in list_available_models(include_unconfigured=False) if r["provider"] == "anthropic"]
    assert rows
    assert all(r["configured"] for r in rows)
    assert any("claude-sonnet" in r["model"] for r in rows)


def test_env_default_without_any_key_prompts_add_provider(monkeypatch):
    for env_key in (
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
        "GEMINI_API_KEY",
        "GROQ_API_KEY",
        "MISTRAL_API_KEY",
    ):
        monkeypatch.setenv(env_key, "")
    monkeypatch.setenv("USE_REAL_LLM", "true")
    monkeypatch.setenv("ACTIVE_PROVIDER", "none")
    monkeypatch.setenv("LOCAL_LLM_ENABLED", "false")
    get_settings.cache_clear()
    from aethos_core.security.credential_vault import get_credential_vault, reset_credential_vault_for_tests

    reset_credential_vault_for_tests()
    get_credential_vault().clear_all_for_tests()
    from aethos_core.llm.model_catalog import env_default_catalog_entry

    entry = env_default_catalog_entry()
    assert entry["configured"] is False
    assert "Connections" in str(entry["label"])


def test_anthropic_model_selection_all_flagships_default():
    from aethos_core.llm.model_selection import get_provider_model_selection

    sel = get_provider_model_selection("anthropic")
    assert sel is not None
    assert sel["provider"] == "anthropic"
    ids = [m["model_id"] for m in sel["models"]]
    assert "claude-sonnet-4-6" in ids
    assert all(m["enabled"] for m in sel["models"])


def test_vault_prefers_validated_key_over_newer_unvalidated(monkeypatch, tmp_path):
    """Stale newer vault rows must not shadow a validated working key."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("USE_REAL_LLM", "true")
    monkeypatch.setenv("CREDENTIALS_DIR", str(tmp_path / "credentials"))
    get_settings.cache_clear()
    monkeypatch.setattr(get_settings(), "anthropic_api_key", "")

    from aethos_core.connections.validation_status import CONFIGURED, INVALID, VALIDATED
    from aethos_core.llm.model_providers import resolve_model_provider_key
    from aethos_core.security.credential_vault import get_credential_vault, reset_credential_vault_for_tests

    reset_credential_vault_for_tests()
    vault = get_credential_vault()
    vault.clear_all_for_tests()
    good = vault.store_api_token(
        provider="anthropic",
        label="Good validated",
        token="sk-ant-good-validated-key-1234567890",
    )
    stale = vault.store_api_token(
        provider="anthropic",
        label="Newer stale",
        token="sk-ant-stale-unvalidated-key-1234567890",
    )
    vault.mark_validation_result(good.credential_id, status=VALIDATED, ok=True)
    vault.mark_validation_result(stale.credential_id, status=CONFIGURED, ok=False)
    assert resolve_model_provider_key("anthropic") == "sk-ant-good-validated-key-1234567890"

    vault.mark_validation_result(stale.credential_id, status=INVALID, ok=False)
    assert resolve_model_provider_key("anthropic") == "sk-ant-good-validated-key-1234567890"


def test_arbiter_pool_requires_two_models_message():
    from aethos_core.arbiter.pool import validate_pool

    out = validate_pool([{"provider": "openai", "model_id": "gpt-4o", "label": "GPT-4o"}])
    assert not out["valid"]
    assert any("at least 2" in e.lower() for e in out["errors"])
