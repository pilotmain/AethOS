# SPDX-License-Identifier: Apache-2.0
"""§2 — multi-provider model keys: catalog, key resolution, routing, vault wiring."""

from __future__ import annotations

import httpx
import pytest

from aethos_core.config import get_settings


@pytest.fixture(autouse=True)
def _clear_settings():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _set_env(monkeypatch, **kv):
    for k, v in kv.items():
        monkeypatch.setenv(k, v)
    get_settings.cache_clear()


def test_anthropic_configured_from_env(monkeypatch):
    _set_env(monkeypatch, ANTHROPIC_API_KEY="sk-ant-test-key-1234567890", USE_REAL_LLM="true")
    from aethos_core.llm.model_providers import anthropic_configured, model_provider_configured

    assert model_provider_configured("anthropic") is True
    assert anthropic_configured() is True


    _set_env(monkeypatch, GROQ_API_KEY="gsk_test_1234567890")
    from aethos_core.llm.model_providers import configured_model_providers, model_provider_configured

    assert model_provider_configured("groq") is True
    assert model_provider_configured("mistral") is False
    assert "groq" in {s.id for s in configured_model_providers()}


def test_key_resolves_env_first(monkeypatch):
    _set_env(monkeypatch, OPENAI_API_KEY="sk-env-key-123456")
    from aethos_core.llm.model_providers import resolve_model_provider_key

    assert resolve_model_provider_key("openai") == "sk-env-key-123456"


def test_catalog_lists_configured_provider_models(monkeypatch):
    _set_env(monkeypatch, MISTRAL_API_KEY="mistral_test_key_123456")
    from aethos_core.llm.model_catalog import list_available_models

    rows = [r for r in list_available_models(include_unconfigured=False) if r["provider"] == "mistral"]
    assert rows, "configured Mistral models should appear in the catalog"
    assert all(r["configured"] for r in rows)
    assert all(r["agent_tool_capable"] for r in rows)


def test_unconfigured_provider_completion_is_honest(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    get_settings.cache_clear()
    from aethos_core.provider.completion import _registry_provider_complete

    out = _registry_provider_complete("hi", provider="groq", model="llama-3.3-70b-versatile")
    assert out.used_llm is False
    assert "Connections" in out.text


def test_registry_completion_routes_and_parses(monkeypatch):
    _set_env(monkeypatch, GROQ_API_KEY="gsk_test_1234567890")

    class _Resp:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [{"message": {"content": "hello from groq"}}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 3},
            }

    class _Client:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, json=None, headers=None):
            assert "groq.com" in url
            assert headers["Authorization"].startswith("Bearer ")
            return _Resp()

    monkeypatch.setattr(httpx, "Client", _Client)
    from aethos_core.provider.completion import _registry_provider_complete

    out = _registry_provider_complete("hi", provider="groq", model="llama-3.3-70b-versatile")
    assert out.used_llm is True
    assert out.text == "hello from groq"
    assert out.provider == "groq"
    assert out.input_tokens == 5 and out.output_tokens == 3


def test_model_providers_registered_in_vault_flow():
    import aethos_core.providers  # noqa: F401 — bootstrap registry

    from aethos_core.providers.base.provider_registry import ProviderRegistry

    managed = set(ProviderRegistry.list_credential_managed_names())
    for pid in (
        "anthropic",
        "gemini",
        "groq",
        "xai",
        "deepseek",
        "cohere",
        "together",
        "fireworks",
        "perplexity",
        "openrouter",
    ):
        assert pid in managed, f"{pid} should be a credential-managed provider"


def test_model_provider_validator_rejects_short_key():
    from aethos_core.providers.cloud.validators import validate_cloud_provider_token

    out = validate_cloud_provider_token("groq", "short")
    assert out["ok"] is False
