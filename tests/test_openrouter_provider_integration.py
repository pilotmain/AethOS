# SPDX-License-Identifier: Apache-2.0
"""OpenRouter must behave like a first-class, vault-aware model provider.

Bug: OpenRouter was a special 'base' provider missing from the model registry, and its
completion key path read only .env — so a UI/vault-stored key validated on the card but was
invisible to chat, the model picker, the selection card (404), and the arbiter.
"""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.llm import model_providers as mp
from aethos_core.llm.model_selection import get_provider_model_selection
from aethos_core.provider import completion as C


def test_openrouter_is_a_registry_provider():
    assert mp.model_provider_spec("openrouter") is not None
    assert mp.is_registry_provider("openrouter") is True
    spec = mp.model_provider_spec("openrouter")
    assert spec.base_url == "https://openrouter.ai/api/v1"
    assert spec.openai_compatible is True


def test_selection_endpoint_no_longer_404s_for_openrouter():
    # get_provider_model_selection returned None (→ HTTP 404) before registration.
    sel = get_provider_model_selection("openrouter")
    assert sel is not None
    assert sel["provider"] == "openrouter"


def test_completion_key_falls_back_to_vault():
    # No .env key, but the vault (via resolve_model_provider_key) has one.
    with patch.object(C, "get_settings") as gs:
        gs.return_value.openrouter_api_key = ""
        with patch(
            "aethos_core.llm.model_providers.resolve_model_provider_key",
            return_value="sk-or-vault-key",
        ):
            assert C._resolved_openrouter_api_key() == "sk-or-vault-key"


def test_completion_key_prefers_env_when_present():
    with patch.object(C, "get_settings") as gs:
        gs.return_value.openrouter_api_key = "sk-or-env-key"
        # vault should not even be consulted, but make it distinct to prove env wins
        with patch(
            "aethos_core.llm.model_providers.resolve_model_provider_key",
            return_value="sk-or-vault-key",
        ):
            assert C._resolved_openrouter_api_key() == "sk-or-env-key"
