# SPDX-License-Identifier: Apache-2.0
"""§9 External KMS / secret-manager backends — envelope encryption of the vault DEK.

When ``KMS_BACKEND`` is set, the vault's data-encryption key (DEK, a Fernet key)
is wrapped (encrypted) by an external Key-Encryption-Key (KEK) managed by AWS KMS,
GCP KMS, or HashiCorp Vault Transit. Only the *wrapped* DEK touches disk; the
plaintext DEK exists in memory just long enough to encrypt/decrypt secrets after
the external KMS unwraps it. Default (empty backend) keeps the local
encrypted-file vault unchanged.

Each backend uses the provider's real SDK via a lazy import so AethOS gains no new
hard dependency; a missing SDK or misconfiguration raises a clear error rather
than silently degrading (fail-closed for a security control).
"""

from __future__ import annotations

import base64


class KmsConfigurationError(RuntimeError):
    """KMS backend selected but not usable (missing SDK or config)."""


def kms_configured() -> bool:
    from aethos_core.config import get_settings

    return bool(get_settings().kms_backend.strip())


def kms_backend_name() -> str:
    from aethos_core.config import get_settings

    return get_settings().kms_backend.strip().lower()


# ────────────────────────────────── AWS KMS ───────────────────────────────────


def _aws_client():
    from aethos_core.config import get_settings

    s = get_settings()
    if not s.aws_kms_key_id:
        raise KmsConfigurationError("KMS_BACKEND=aws requires AWS_KMS_KEY_ID")
    try:
        import boto3
    except ImportError as exc:  # pragma: no cover - needs boto3
        raise KmsConfigurationError("boto3 not installed (pip install 'aethos[cloud]')") from exc
    kwargs = {"region_name": s.aws_region} if s.aws_region else {}
    return boto3.client("kms", **kwargs), s.aws_kms_key_id


def _aws_wrap(plaintext: bytes) -> bytes:
    client, key_id = _aws_client()
    return client.encrypt(KeyId=key_id, Plaintext=plaintext)["CiphertextBlob"]


def _aws_unwrap(blob: bytes) -> bytes:
    client, _ = _aws_client()
    return client.decrypt(CiphertextBlob=blob)["Plaintext"]


# ────────────────────────────────── GCP KMS ───────────────────────────────────


def _gcp_client():
    from aethos_core.config import get_settings

    s = get_settings()
    if not s.gcp_kms_key_name:
        raise KmsConfigurationError("KMS_BACKEND=gcp requires GCP_KMS_KEY_NAME")
    try:
        from google.cloud import kms
    except ImportError as exc:  # pragma: no cover - needs google-cloud-kms
        raise KmsConfigurationError("google-cloud-kms not installed") from exc
    return kms.KeyManagementServiceClient(), s.gcp_kms_key_name


def _gcp_wrap(plaintext: bytes) -> bytes:
    client, name = _gcp_client()
    return client.encrypt(request={"name": name, "plaintext": plaintext}).ciphertext


def _gcp_unwrap(blob: bytes) -> bytes:
    client, name = _gcp_client()
    return client.decrypt(request={"name": name, "ciphertext": blob}).plaintext


# ─────────────────────────────── Vault Transit ────────────────────────────────


def _vault_client():
    from aethos_core.config import get_settings

    s = get_settings()
    if not (s.vault_kms_addr and s.vault_kms_token):
        raise KmsConfigurationError("KMS_BACKEND=vault requires VAULT_KMS_ADDR + VAULT_KMS_TOKEN")
    try:
        import hvac
    except ImportError as exc:  # pragma: no cover - needs hvac
        raise KmsConfigurationError("hvac not installed (pip install hvac)") from exc
    return hvac.Client(url=s.vault_kms_addr, token=s.vault_kms_token), s.vault_kms_transit_key


def _vault_wrap(plaintext: bytes) -> bytes:
    client, key = _vault_client()
    resp = client.secrets.transit.encrypt_data(
        name=key, plaintext=base64.b64encode(plaintext).decode()
    )
    return resp["data"]["ciphertext"].encode()


def _vault_unwrap(blob: bytes) -> bytes:
    client, key = _vault_client()
    resp = client.secrets.transit.decrypt_data(name=key, ciphertext=blob.decode())
    return base64.b64decode(resp["data"]["plaintext"])


# ─────────────────────────────────── dispatch ─────────────────────────────────

_WRAPPERS = {"aws": _aws_wrap, "gcp": _gcp_wrap, "vault": _vault_wrap}
_UNWRAPPERS = {"aws": _aws_unwrap, "gcp": _gcp_unwrap, "vault": _vault_unwrap}


def wrap_dek(plaintext: bytes) -> bytes:
    backend = kms_backend_name()
    fn = _WRAPPERS.get(backend)
    if fn is None:
        raise KmsConfigurationError(f"Unknown KMS_BACKEND: {backend!r}")
    return fn(plaintext)


def unwrap_dek(wrapped: bytes) -> bytes:
    backend = kms_backend_name()
    fn = _UNWRAPPERS.get(backend)
    if fn is None:
        raise KmsConfigurationError(f"Unknown KMS_BACKEND: {backend!r}")
    return fn(wrapped)
