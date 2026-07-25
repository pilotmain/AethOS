# SPDX-License-Identifier: Apache-2.0
"""Credential vault cross-process — api write visible to worker read."""

from __future__ import annotations

import os

import pytest

from aethos_core.config import get_settings
from aethos_core.security.credential_vault import (
    CredentialVault,
    get_credential_vault,
    reset_credential_vault_for_tests,
)
from aethos_core.tenancy.tenant_data_store import reset_for_tests


def _postgres_url() -> str:
    return str(
        os.environ.get("TEST_DATABASE_URL", "") or os.environ.get("DATABASE_URL", "") or ""
    ).strip()


@pytest.fixture
def postgres_vault_env(monkeypatch, tmp_path):
    url = _postgres_url()
    if not url:
        pytest.skip("DATABASE_URL or TEST_DATABASE_URL required for Postgres vault tests")
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("AETHOS_VAULT_KEY", "test-vault-key-cross-process")
    get_settings.cache_clear()
    reset_for_tests()
    reset_credential_vault_for_tests()
    vault = get_credential_vault()
    vault.clear_all_for_tests()
    yield vault
    vault.clear_all_for_tests()
    reset_credential_vault_for_tests()
    reset_for_tests()


def test_api_write_worker_read_postgres(postgres_vault_env):
    vault = postgres_vault_env
    rec = vault.store_api_token(provider="vercel", label="staging", token="vercel-test-token-abc")
    cid = rec.credential_id

    reset_for_tests()
    get_settings.cache_clear()
    reset_credential_vault_for_tests()

    reader = CredentialVault()
    secret = reader.retrieve_secret(cid)
    assert secret is not None
    assert secret.get("token") == "vercel-test-token-abc"
