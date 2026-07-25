# SPDX-License-Identifier: Apache-2.0
"""Regression: resolving a non-railway/vercel provider token must not infinitely recurse.

The generic cloud ApiTokenAuthAdapter.get_api_token used to delegate back to
provider_runtime.get_provider_api_token, which calls the adapter again — an infinite loop
that surfaced to operators as "Anthropic validation internal error" (RecursionError).
"""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.security.credential_vault import CredentialVault, reset_credential_vault_for_tests


@pytest.fixture
def vault_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("CREDENTIALS_DIR", str(tmp_path / "credentials"))
    monkeypatch.setenv(
        "AETHOS_VAULT_KEY",
        "test-vault-key-no-recursion-0123456789",  # gitleaks:allow - synthetic fixture
    )
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    reset_credential_vault_for_tests()
    get_settings.cache_clear()
    yield tmp_path / "credentials"
    reset_credential_vault_for_tests()
    get_settings.cache_clear()


def test_anthropic_token_resolves_without_recursion(vault_paths):
    vault = CredentialVault(vault_paths)
    rec = vault.store_api_token(provider="anthropic", label="Anthropic", token="sk-ant-test-1234567890abcdef")
    reset_credential_vault_for_tests()
    CredentialVault(vault_paths)

    # Direct adapter read — the leaf resolver must return the token, not recurse.
    from aethos_core.providers.cloud.auth_adapter import ApiTokenAuthAdapter

    adapter = ApiTokenAuthAdapter(provider="anthropic")
    assert adapter.get_api_token(rec.credential_id) == "sk-ant-test-1234567890abcdef"

    # End-to-end resolver path used by "validate connections".
    from aethos_core.execution_brain.cloud_agent_bridge import resolve_provider_token

    token, err = resolve_provider_token("anthropic", require_validated=False)
    assert err is None
    assert token == "sk-ant-test-1234567890abcdef"


def test_get_api_token_wrong_provider_returns_none(vault_paths):
    vault = CredentialVault(vault_paths)
    rec = vault.store_api_token(provider="anthropic", label="Anthropic", token="sk-ant-xyz-1234567890")
    from aethos_core.providers.cloud.auth_adapter import ApiTokenAuthAdapter

    # An adapter for a different provider must not return another provider's secret.
    assert ApiTokenAuthAdapter(provider="openai").get_api_token(rec.credential_id) is None
    assert ApiTokenAuthAdapter(provider="anthropic").get_api_token("cred-does-not-exist") is None
