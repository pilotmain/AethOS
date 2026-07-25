# SPDX-License-Identifier: Apache-2.0
"""Regression: storing a credential must succeed on the Postgres (hosted) backend.

Reproduces the production bug where, with DATABASE_URL set (hosted Railway), the vault
wrote the secret to Postgres correctly but _verify_secret_persistence only checked for a
local FILE — so every store_api_token raised CredentialPersistenceError
('Encrypted secret file missing after write') and the credential was rolled back, leaving
the vault permanently empty.
"""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.security import credential_vault as cv
from aethos_core.security.credential_vault import CredentialVault
from aethos_core.tenancy import tenant_data_store as tds


@pytest.fixture
def fake_postgres_vault(monkeypatch, tmp_path):
    monkeypatch.setenv("AETHOS_VAULT_KEY", "test-vault-key-postgres-persistence-0123456789")
    get_settings.cache_clear()
    # Force the Postgres code path and a no-keyring environment (like the Railway container).
    monkeypatch.setattr(cv, "_vault_uses_postgres", lambda: True)
    monkeypatch.setattr(cv, "_keyring_available", lambda: False)

    store: dict[tuple[str, str, str], object] = {}

    def _set_record(namespace, record_key, payload, *, tenant_id=None):
        store[(namespace, record_key, str(tenant_id))] = payload

    def _get_record(namespace, record_key, *, tenant_id=None, default=None):
        return store.get((namespace, record_key, str(tenant_id)), default)

    def _delete_record(namespace, record_key, *, tenant_id=None):
        return store.pop((namespace, record_key, str(tenant_id)), None) is not None

    monkeypatch.setattr(tds, "set_record", _set_record)
    monkeypatch.setattr(tds, "get_record", _get_record)
    monkeypatch.setattr(tds, "delete_record", _delete_record)

    yield CredentialVault(tmp_path / "vault")
    get_settings.cache_clear()


def test_store_api_token_succeeds_on_postgres_backend(fake_postgres_vault):
    vault = fake_postgres_vault
    rec = vault.store_api_token(
        provider="anthropic",
        label="primary",
        token="sk-ant-postgres-roundtrip-abcdef 1234567890".replace(" ", ""),
    )
    assert rec.credential_id
    assert rec.storage == "postgres_encrypted"
    # Round-trips back out of the (simulated) Postgres store.
    secret = vault.retrieve_secret(rec.credential_id)
    assert secret is not None
    assert secret["token"].startswith("sk-ant-postgres-roundtrip")


def test_verify_secret_persistence_accepts_postgres_presence(fake_postgres_vault, monkeypatch):
    """The verifier must treat a Postgres-backed (file-less) secret as present."""
    vault = fake_postgres_vault
    monkeypatch.setattr(
        vault,
        "inspect_secret_storage",
        lambda cid: {"has_encrypted_secret": True, "decryptable": True},
    )
    monkeypatch.setattr(vault, "_read_secret", lambda cid: {"token": "sk-ant-xyz"})
    out = vault._verify_secret_persistence("cred-x", "sk-ant-xyz")
    assert out["ok"] is True


def test_verify_secret_persistence_fails_when_truly_absent(fake_postgres_vault, monkeypatch):
    vault = fake_postgres_vault
    monkeypatch.setattr(
        vault,
        "inspect_secret_storage",
        lambda cid: {"has_encrypted_secret": False, "decryptable": False},
    )
    monkeypatch.setattr(vault, "_read_secret", lambda cid: None)
    out = vault._verify_secret_persistence("cred-x", "sk-ant-xyz")
    assert out["ok"] is False
    assert out["failure_class"] == "encrypted_secret_missing"
