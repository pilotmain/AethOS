# SPDX-License-Identifier: Apache-2.0
"""§9 external KMS option — envelope encryption of the vault DEK."""

from __future__ import annotations

import base64

import pytest

import aethos_core.security.credential_vault as vault
import aethos_core.security.kms_backend as kms
from aethos_core.config import get_settings


@pytest.fixture
def kms_env(tmp_path, monkeypatch):
    monkeypatch.setenv("CREDENTIALS_DIR", str(tmp_path / "credentials"))
    monkeypatch.setenv("KMS_BACKEND", "aws")
    monkeypatch.setenv("AWS_KMS_KEY_ID", "test-key")
    get_settings.cache_clear()
    vault._DEK_CACHE = None
    # Fake KEK: a reversible transform standing in for the external KMS.
    monkeypatch.setattr(kms, "wrap_dek", lambda pt: b"WRAPPED:" + base64.b64encode(pt))
    monkeypatch.setattr(kms, "unwrap_dek", lambda blob: base64.b64decode(blob[len(b"WRAPPED:"):]))
    yield tmp_path
    vault._DEK_CACHE = None
    get_settings.cache_clear()


def test_envelope_roundtrip_and_only_wrapped_on_disk(kms_env):
    token = vault._encrypt(b"super-secret-token")
    assert vault._decrypt(token) == b"super-secret-token"
    # Only the wrapped DEK exists; no plaintext key file.
    assert vault._wrapped_machine_key_path().is_file()
    assert not vault.machine_key_path().is_file()
    # The wrapped blob is actually wrapped (not the raw fernet key).
    assert vault._wrapped_machine_key_path().read_bytes().startswith(b"WRAPPED:")


def test_migrates_existing_plaintext_key(kms_env):
    # Simulate a pre-existing local (plaintext) DEK, then switch to KMS.
    from cryptography.fernet import Fernet

    existing = Fernet.generate_key()
    p = vault.machine_key_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(existing)
    # Encrypt something with the existing key via the local path...
    ciphertext = Fernet(existing).encrypt(b"legacy")
    # ...now loading under KMS must wrap the SAME key and still decrypt it.
    vault._DEK_CACHE = None
    assert vault._decrypt(ciphertext) == b"legacy"
    assert not p.is_file()  # plaintext dropped after migration
    assert vault._wrapped_machine_key_path().is_file()


def test_local_mode_unchanged(tmp_path, monkeypatch):
    monkeypatch.setenv("CREDENTIALS_DIR", str(tmp_path / "credentials"))
    monkeypatch.delenv("KMS_BACKEND", raising=False)
    get_settings.cache_clear()
    vault._DEK_CACHE = None
    try:
        token = vault._encrypt(b"local-secret")
        assert vault._decrypt(token) == b"local-secret"
        assert vault.machine_key_path().is_file()
    finally:
        get_settings.cache_clear()


def test_unknown_backend_raises(monkeypatch):
    monkeypatch.setenv("KMS_BACKEND", "bogus")
    get_settings.cache_clear()
    try:
        with pytest.raises(kms.KmsConfigurationError):
            kms.wrap_dek(b"x")
    finally:
        get_settings.cache_clear()
