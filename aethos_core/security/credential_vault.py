# SPDX-License-Identifier: Apache-2.0
"""Local credential vault — encrypted file with optional OS keyring."""

from __future__ import annotations

import base64
import json
import logging
import os
import stat
import tempfile
import threading
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.connections.models import CredentialRecord, CredentialType
from aethos_core.connections.validation_status import CONFIGURED, PERSISTENCE_FAILED
from aethos_core.security.credential_paths import (
    credential_index_path,
    credential_root,
    credential_secret_dir,
    credential_secret_path,
    machine_key_path,
)
from aethos_core.security.secret_redaction import mask_secret, safe_log_message

_log = logging.getLogger(__name__)
_VAULT_IO_LOCK = threading.RLock()


def _audit_vault(action: str, provider: str, credential_id: str) -> None:
    """Best-effort write to the §3 unified audit ledger (never blocks vault I/O)."""
    try:
        from aethos_core.observability.audit_ledger import record_audit_event

        record_audit_event(action=action, target=credential_id, metadata={"provider": provider})
    except Exception:  # noqa: BLE001
        pass


class CredentialPersistenceError(RuntimeError):
    """Encrypted secret could not be durably persisted or verified."""

    def __init__(self, detail: str, *, diagnostics: dict[str, Any] | None = None) -> None:
        super().__init__(detail)
        self.diagnostics = diagnostics or {}


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    """Atomic JSON write — unique temp name avoids reload races on credentials.json.tmp."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        os.chmod(tmp_name, stat.S_IRUSR | stat.S_IWUSR)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


class CredentialVault:
    def __init__(self, root_dir: Path | None = None) -> None:
        self._root = root_dir or credential_root()
        self._index_path = credential_index_path()
        self._secret_dir = credential_secret_dir()
        self._records: dict[str, CredentialRecord] = {}
        # Preferred auth method is per-tenant: {owner_id: {provider: method}}.
        self._preferred: dict[str, dict[str, str]] = {}
        self._lock = _VAULT_IO_LOCK
        self._load()

    # ── tenancy ────────────────────────────────────────────────────────────
    # Every owner-sensitive operation is scoped to the *current* tenant. In
    # single-tenant mode (flag off) this is always "default", so the vault holds
    # one owner and behavior is identical to before. In multi-tenant mode the
    # tenant comes from the request context (or a detached job/arbiter's stamp),
    # and a credential owned by tenant A is invisible to tenant B — no method
    # returns, reads, or revokes another tenant's credential.

    @staticmethod
    def _current_owner() -> str:
        from aethos_core.config import get_settings
        from aethos_core.tenancy import DEFAULT_TENANT, get_current_tenant

        if not get_settings().multi_tenant_enabled:
            return DEFAULT_TENANT
        return get_current_tenant()

    def _owned(self, rec: CredentialRecord | None) -> bool:
        return rec is not None and rec.owner_id == self._current_owner()

    def _get_owned(self, credential_id: str) -> CredentialRecord | None:
        """Metadata lookup that refuses cross-tenant access (revoked included)."""
        rec = self._records.get(credential_id)
        return rec if self._owned(rec) else None

    def clear_all_for_tests(self) -> None:
        self._records.clear()
        self._preferred.clear()
        if _vault_uses_postgres():
            from aethos_core.tenancy import DEFAULT_TENANT
            from aethos_core.tenancy.tenant_data_store import clear_namespace

            clear_namespace(_NS_VAULT_INDEX, tenant_id=DEFAULT_TENANT)
            clear_namespace(_NS_VAULT_SECRET, tenant_id=DEFAULT_TENANT)
            return
        if self._index_path.is_file():
            self._index_path.unlink()
        if self._secret_dir.is_dir():
            for p in self._secret_dir.glob("*"):
                p.unlink()

    def list_credentials(self, *, provider: str | None = None) -> list[CredentialRecord]:
        owner = self._current_owner()
        out = [r for r in self._records.values() if not r.revoked and r.owner_id == owner]
        if provider:
            out = [r for r in out if r.provider == provider]
        out.sort(key=lambda r: r.created_at, reverse=True)
        return out

    def find_unique_owner_for_provider(self, provider: str) -> str | None:
        """When exactly one tenant owns active credentials for a provider, return that owner."""
        owners = {
            r.owner_id
            for r in self._records.values()
            if not r.revoked and r.provider == provider
        }
        if len(owners) != 1:
            return None
        return next(iter(owners))

    def get(self, credential_id: str) -> CredentialRecord | None:
        rec = self._get_owned(credential_id)
        if not rec or rec.revoked:
            return None
        return rec

    def get_preferred_method(self, provider: str) -> str:
        return self._preferred.get(self._current_owner(), {}).get(provider, "ask")

    def set_preferred_method(self, provider: str, method: str) -> None:
        self._preferred.setdefault(self._current_owner(), {})[provider] = method
        self._persist()

    def store_api_token(
        self,
        *,
        provider: str,
        label: str,
        token: str,
        scope: list[str] | None = None,
        write_allowed: bool = False,
        masked_identifier: str = "",
    ) -> CredentialRecord:
        token = (token or "").strip()
        if not token:
            raise ValueError("Token value is required.")
        credential_id = f"cred-{uuid4().hex[:12]}"
        masked = masked_identifier or mask_secret(token, visible=4)
        record = CredentialRecord(
            credential_id=credential_id,
            provider=provider,
            type=CredentialType.API_TOKEN,
            label=label.strip() or f"{provider} API token",
            owner_id=self._current_owner(),
            scope=list(scope or ["read_projects", "read_logs"]),
            write_allowed=write_allowed,
            storage=self._storage_label(),
            masked_identifier=masked,
            validation_status=CONFIGURED,
            updated_at=time(),
        )
        self._records[credential_id] = record
        self._write_secret(credential_id, {"token": token})
        persistence = self._verify_secret_persistence(credential_id, token)
        if not persistence.get("ok"):
            self._delete_secret(credential_id)
            del self._records[credential_id]
            raise CredentialPersistenceError(
                persistence.get("detail") or "Secret persistence validation failed.",
                diagnostics=persistence,
            )
        self._persist()
        _log.info("credential_saved provider=%s type=api_token id=%s", provider, credential_id)
        _audit_vault("vault.write", provider, credential_id)
        return record

    def retrieve_secret(self, credential_id: str) -> dict[str, str] | None:
        rec = self.get(credential_id)
        if not rec:
            return None
        secret, _diag = self._read_secret_with_diagnostics(credential_id)
        if secret is None:
            return None
        now = time()
        last = float(rec.last_used_at or 0)
        if now - last >= 30.0:
            rec.last_used_at = now
            self._persist()
        return secret

    def inspect_secret_storage(self, credential_id: str) -> dict[str, Any]:
        rec = self._get_owned(credential_id)
        has_metadata = rec is not None and not rec.revoked
        enc_path = credential_secret_path(credential_id)
        has_encrypted_file = enc_path.is_file()
        if _vault_uses_postgres() and rec is not None:
            from aethos_core.tenancy.tenant_data_store import get_record

            blob = get_record(_NS_VAULT_SECRET, credential_id, tenant_id=rec.owner_id, default=None)
            has_encrypted_file = bool(blob)
        keyring_present = False
        if _keyring_available():
            import keyring

            keyring_present = bool(keyring.get_password("aethos", credential_id))
        secret, read_diag = self._read_secret_with_diagnostics(credential_id)
        token = str((secret or {}).get("token") or "").strip()
        decryptable = bool(token)
        failure_class: str | None = None
        if has_metadata and not has_encrypted_file and not keyring_present:
            failure_class = "encrypted_secret_missing"
        elif has_metadata and (has_encrypted_file or keyring_present) and not decryptable:
            failure_class = str(read_diag.get("failure_class") or "decrypt_failed")
        elif has_metadata and not decryptable:
            failure_class = "secret_missing"
        return {
            "credential_id": credential_id,
            "has_metadata": has_metadata,
            "has_encrypted_secret": has_encrypted_file or keyring_present,
            "decryptable": decryptable,
            "vault_path": str(self._root),
            "secret_file_path": str(enc_path) if has_encrypted_file else None,
            "storage_backend": self._storage_label(),
            "failure_class": failure_class,
            "auth_source": "encrypted_vault" if decryptable else "metadata_only",
        }

    def revoke(self, credential_id: str) -> bool:
        rec = self._get_owned(credential_id)
        if not rec:
            return False
        rec.revoked = True
        self._delete_secret(credential_id)
        self._persist()
        _log.info("credential_revoked id=%s provider=%s", credential_id, rec.provider)
        return True

    def mark_test_result(self, credential_id: str, *, ok: bool) -> None:
        rec = self._get_owned(credential_id)
        if not rec:
            return
        rec.last_tested_at = time()
        rec.last_test_ok = ok
        rec.updated_at = time()
        self._persist()

    def mark_validation_result(
        self,
        credential_id: str,
        *,
        status: str,
        ok: bool,
        diagnostics: dict[str, Any] | None = None,
    ) -> None:
        rec = self._get_owned(credential_id)
        if not rec:
            return
        rec.validation_status = status
        rec.last_validated_at = time()
        rec.last_tested_at = time()
        rec.last_test_ok = ok
        rec.updated_at = time()
        if diagnostics is not None:
            rec.validation_diagnostics = dict(diagnostics)
        self._persist()

    def rotate_api_token(self, credential_id: str, *, token: str) -> CredentialRecord | None:
        rec = self.get(credential_id)
        if not rec:
            return None
        token = (token or "").strip()
        if not token:
            raise ValueError("Token value is required.")
        self._write_secret(credential_id, {"token": token})
        persistence = self._verify_secret_persistence(credential_id, token)
        if not persistence.get("ok"):
            rec.validation_status = PERSISTENCE_FAILED
            rec.validation_diagnostics = persistence
            rec.updated_at = time()
            self._persist()
            raise CredentialPersistenceError(
                persistence.get("detail") or "Secret persistence validation failed on rotate.",
                diagnostics=persistence,
            )
        rec.masked_identifier = mask_secret(token, visible=4)
        rec.validation_status = CONFIGURED
        rec.updated_at = time()
        self._persist()
        _log.info("credential_rotated id=%s provider=%s", credential_id, rec.provider)
        return rec

    def diagnostics(self) -> dict[str, Any]:
        owner = self._current_owner()
        active = [r for r in self._records.values() if not r.revoked and r.owner_id == owner]
        return {
            "vault_path": str(self._root),
            "credential_count": len(active),
            "storage_backend": self._storage_label(),
        }

    def _load(self) -> None:
        if _vault_uses_postgres():
            from aethos_core.tenancy import DEFAULT_TENANT
            from aethos_core.tenancy.tenant_data_store import get_record

            raw = get_record(
                _NS_VAULT_INDEX,
                _VAULT_INDEX_KEY,
                tenant_id=DEFAULT_TENANT,
                default={},
            )
            if not isinstance(raw, dict):
                return
            self._preferred = self._load_preferred(raw.get("preferred"))
            items = raw.get("credentials") or []
        elif not self._index_path.is_file():
            return
        else:
            try:
                raw = json.loads(self._index_path.read_text(encoding="utf-8"))
            except Exception:
                _log.exception("credential_index_load_failed path=%s", self._index_path)
                return
            self._preferred = self._load_preferred(raw.get("preferred"))
            items = raw.get("credentials") or []
        for item in items:
            try:
                rec = CredentialRecord(
                    credential_id=str(item["credential_id"]),
                    provider=str(item["provider"]),
                    type=CredentialType(str(item["type"])),
                    label=str(item.get("label") or ""),
                    # Legacy records (pre-multi-tenant) have no owner_id; they
                    # belong to the operator/default tenant — the migration step.
                    owner_id=str(item.get("owner_id") or "default"),
                    created_at=float(item.get("created_at") or time()),
                    last_used_at=item.get("last_used_at"),
                    last_tested_at=item.get("last_tested_at"),
                    last_test_ok=item.get("last_test_ok"),
                    expires_at=item.get("expires_at"),
                    revoked=bool(item.get("revoked")),
                    scope=list(item.get("scope") or []),
                    write_allowed=bool(item.get("write_allowed")),
                    storage=str(item.get("storage") or "encrypted_file"),
                    masked_identifier=str(item.get("masked_identifier") or ""),
                    validation_status=str(item.get("validation_status") or CONFIGURED),
                    last_validated_at=item.get("last_validated_at"),
                    updated_at=item.get("updated_at"),
                    validation_diagnostics=dict(item.get("validation_diagnostics") or {}),
                )
                if not rec.revoked:
                    self._records[rec.credential_id] = rec
            except Exception:
                _log.exception("credential_record_load_failed item=%s", safe_log_message(str(item)))

    @staticmethod
    def _load_preferred(raw: Any) -> dict[str, dict[str, str]]:
        """Parse the preferred-method map, migrating the legacy flat shape.

        Legacy: {provider: method}. New: {owner_id: {provider: method}}. A legacy
        flat map is attributed to the operator/default tenant.
        """
        if not isinstance(raw, dict):
            return {}
        if raw and all(isinstance(v, dict) for v in raw.values()):
            return {str(k): {str(p): str(m) for p, m in v.items()} for k, v in raw.items()}
        # Flat legacy shape → default tenant owns it.
        return {"default": {str(p): str(m) for p, m in raw.items() if isinstance(m, str)}}

    def _persist(self) -> None:
        payload = {
            "preferred": self._preferred,
            "credentials": [r.to_public_dict() for r in self._records.values()],
        }
        with self._lock:
            if _vault_uses_postgres():
                from aethos_core.tenancy import DEFAULT_TENANT
                from aethos_core.tenancy.tenant_data_store import set_record

                set_record(
                    _NS_VAULT_INDEX,
                    _VAULT_INDEX_KEY,
                    payload,
                    tenant_id=DEFAULT_TENANT,
                )
                return
            _atomic_write_json(self._index_path, payload)

    def _storage_label(self) -> str:
        if _vault_uses_postgres():
            return "postgres_encrypted"
        if _keyring_available():
            return "local_keychain"
        return "encrypted_file"

    def _verify_secret_persistence(self, credential_id: str, expected_token: str) -> dict[str, Any]:
        enc_path = credential_secret_path(credential_id)
        secret_file_exists = enc_path.is_file()
        storage = self.inspect_secret_storage(credential_id)
        decryptable = bool(storage.get("decryptable"))
        # Backend-aware presence: the secret may live in Postgres (hosted) or the OS keyring,
        # not only as a local file. Checking the file alone falsely fails Postgres-backed writes.
        secret_present = bool(storage.get("has_encrypted_secret")) or secret_file_exists
        fernet_valid = decryptable
        non_empty = False
        if decryptable:
            secret = self._read_secret(credential_id)
            token = str((secret or {}).get("token") or "").strip()
            non_empty = bool(token)
            if token != expected_token.strip():
                return {
                    "ok": False,
                    "secret_file_exists": secret_file_exists,
                    "decryptable": False,
                    "non_empty": non_empty,
                    "fernet_valid": False,
                    "detail": "Persisted token does not round-trip after write.",
                    "failure_class": "persistence_roundtrip_failed",
                }
        if not secret_present:
            return {
                "ok": False,
                "secret_file_exists": False,
                "decryptable": False,
                "non_empty": False,
                "fernet_valid": False,
                "detail": "Encrypted secret missing after write (no file, Postgres row, or keyring entry).",
                "failure_class": "encrypted_secret_missing",
            }
        if not decryptable or not non_empty:
            return {
                "ok": False,
                "secret_file_exists": secret_file_exists,
                "decryptable": decryptable,
                "non_empty": non_empty,
                "fernet_valid": fernet_valid,
                "detail": "Encrypted secret not decryptable after write.",
                "failure_class": storage.get("failure_class") or "decrypt_failed",
            }
        return {
            "ok": True,
            "secret_file_exists": secret_file_exists,
            "decryptable": True,
            "non_empty": True,
            "fernet_valid": True,
            "secret_file_path": str(enc_path),
            "vault_path": str(self._root),
        }

    def _write_secret(self, credential_id: str, payload: dict[str, str]) -> None:
        raw = json.dumps(payload)
        enc = _encrypt(raw.encode("utf-8"))
        rec = self._records.get(credential_id)
        owner = rec.owner_id if rec else self._current_owner()
        if _vault_uses_postgres():
            import base64

            from aethos_core.tenancy.tenant_data_store import set_record

            set_record(
                _NS_VAULT_SECRET,
                credential_id,
                base64.b64encode(enc).decode("ascii"),
                tenant_id=owner,
            )
        else:
            self._secret_dir.mkdir(parents=True, exist_ok=True)
            path = credential_secret_path(credential_id)
            path.write_bytes(enc)
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        if _keyring_available():
            import keyring

            keyring.set_password("aethos", credential_id, raw)

    def _read_secret_with_diagnostics(self, credential_id: str) -> tuple[dict[str, str] | None, dict[str, Any]]:
        diag: dict[str, Any] = {}
        if _keyring_available():
            import keyring

            raw = keyring.get_password("aethos", credential_id)
            if raw:
                try:
                    return json.loads(raw), diag
                except json.JSONDecodeError:
                    diag["failure_class"] = "decrypt_failed"
                    return None, diag
        rec = self._records.get(credential_id)
        owner = rec.owner_id if rec else self._current_owner()
        if _vault_uses_postgres():
            import base64

            from aethos_core.tenancy.tenant_data_store import get_record

            blob = get_record(_NS_VAULT_SECRET, credential_id, tenant_id=owner, default=None)
            if not blob:
                diag["failure_class"] = "encrypted_secret_missing"
                diag["store_sync"] = "postgres_missing_row"
                return None, diag
            try:
                enc = base64.b64decode(str(blob).encode("ascii"))
                plain = _decrypt(enc)
                return json.loads(plain.decode("utf-8")), diag
            except Exception:
                _log.exception("credential_secret_read_failed id=%s", credential_id)
                diag["failure_class"] = "decrypt_failed"
                return None, diag
        path = credential_secret_path(credential_id)
        if not path.is_file():
            diag["failure_class"] = "encrypted_secret_missing"
            return None, diag
        try:
            plain = _decrypt(path.read_bytes())
            return json.loads(plain.decode("utf-8")), diag
        except Exception:
            _log.exception("credential_secret_read_failed id=%s", credential_id)
            diag["failure_class"] = "decrypt_failed"
            return None, diag

    def _read_secret(self, credential_id: str) -> dict[str, str] | None:
        secret, _diag = self._read_secret_with_diagnostics(credential_id)
        return secret

    def _delete_secret(self, credential_id: str) -> None:
        if _vault_uses_postgres():
            rec = self._records.get(credential_id)
            owner = rec.owner_id if rec else self._current_owner()
            from aethos_core.tenancy.tenant_data_store import delete_record

            delete_record(_NS_VAULT_SECRET, credential_id, tenant_id=owner)
        if _keyring_available():
            import keyring

            try:
                keyring.delete_password("aethos", credential_id)
            except Exception:
                pass
        path = credential_secret_path(credential_id)
        if path.is_file():
            path.unlink()
        rec = self._records.get(credential_id)
        _audit_vault("vault.delete", rec.provider if rec else "unknown", credential_id)


def _keyring_available() -> bool:
    try:
        import keyring  # noqa: F401

        return True
    except ImportError:
        return False


def _fernet():
    from cryptography.fernet import Fernet

    return Fernet


_DEK_CACHE: bytes | None = None


def _wrapped_machine_key_path() -> Path:
    p = machine_key_path()
    return p.with_name(p.name + ".wrapped")


def _vault_uses_postgres() -> bool:
    from aethos_core.storage.shared_store_backend import uses_postgres_shared_store

    return uses_postgres_shared_store()


_NS_VAULT_INDEX = "credential_vault_index"
_NS_VAULT_SECRET = "credential_vault_secret"
_VAULT_INDEX_KEY = "_global"


def _vault_key_from_env() -> bytes | None:
    import os

    raw = str(os.environ.get("AETHOS_VAULT_KEY", "") or "").strip()
    if not raw:
        from aethos_core.config import get_settings

        raw = str(getattr(get_settings(), "aethos_vault_key", "") or "").strip()
    if not raw:
        return None
    from base64 import urlsafe_b64encode
    from hashlib import sha256

    return urlsafe_b64encode(sha256(raw.encode("utf-8")).digest())


def _load_or_create_machine_key() -> bytes:
    """Return the Fernet DEK. With KMS_BACKEND set, the DEK is envelope-encrypted
    by the external KEK and only the wrapped blob is stored on disk (§9). Default
    (no KMS) keeps the plaintext key file behavior unchanged.

    On hosted / shared Postgres, ``AETHOS_VAULT_KEY`` must be set identically on
    every process so worker and api can decrypt the same vault records.
    """
    env_key = _vault_key_from_env()
    if env_key is not None:
        return env_key

    global _DEK_CACHE
    from aethos_core.production.deployment_mode import is_hosted_deployment
    from aethos_core.storage.shared_store_backend import uses_postgres_shared_store

    if is_hosted_deployment() or uses_postgres_shared_store():
        raise RuntimeError(
            "AETHOS_VAULT_KEY must be set on hosted deployments so api and worker "
            "decrypt the same credential vault. Set an identical secret on every service."
        )

    from aethos_core.security.kms_backend import kms_configured, unwrap_dek, wrap_dek

    if kms_configured():
        if _DEK_CACHE is not None:
            return _DEK_CACHE
        wrapped_path = _wrapped_machine_key_path()
        plain_path = machine_key_path()
        if wrapped_path.is_file():
            dek = unwrap_dek(wrapped_path.read_bytes())
        elif plain_path.is_file():
            # Migrate an existing local DEK under KMS without losing access to
            # already-encrypted secrets: wrap the same key, then drop the plaintext.
            dek = plain_path.read_bytes()
            wrapped_path.write_bytes(wrap_dek(dek))
            os.chmod(wrapped_path, stat.S_IRUSR | stat.S_IWUSR)
            plain_path.unlink()
        else:
            dek = _fernet().generate_key()
            wrapped_path.parent.mkdir(parents=True, exist_ok=True)
            wrapped_path.write_bytes(wrap_dek(dek))
            os.chmod(wrapped_path, stat.S_IRUSR | stat.S_IWUSR)
        _DEK_CACHE = dek
        return dek

    path = machine_key_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        return path.read_bytes()
    key = _fernet().generate_key()
    path.write_bytes(key)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    return key


def _encrypt(data: bytes) -> bytes:
    from cryptography.fernet import Fernet

    key = _load_or_create_machine_key()
    return Fernet(key).encrypt(data)


def _decrypt(data: bytes) -> bytes:
    from cryptography.fernet import Fernet

    key = _load_or_create_machine_key()
    return Fernet(key).decrypt(data)


def _default_root() -> Path:
    return credential_root()


_vault: CredentialVault | None = None


def get_credential_vault_diagnostics() -> dict[str, Any]:
    """Safe vault readiness — no secrets."""
    root = credential_root()
    crypto = "missing"
    try:
        from cryptography.fernet import Fernet  # noqa: F401

        crypto = "installed"
    except ImportError:
        crypto = "missing"
    keyring = "installed" if _keyring_available() else "missing"
    can_write = False
    credentials_dir_exists = root.is_dir()
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe = root / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        can_write = True
        credentials_dir_exists = True
    except OSError:
        can_write = False
    backend = "local_keychain" if _keyring_available() else "encrypted_file"
    available = crypto == "installed" and can_write
    return {
        "available": available,
        "backend": backend,
        "credentials_dir": str(root),
        "credentials_dir_exists": credentials_dir_exists,
        "can_write": can_write,
        "dependencies": {
            "cryptography": crypto,
            "keyring": keyring,
        },
    }


def get_credential_vault() -> CredentialVault:
    global _vault
    if _vault is None:
        _vault = CredentialVault(_default_root())
    return _vault


def reload_credential_vault_from_disk() -> CredentialVault:
    """Drop in-memory vault cache and reload encrypted credentials from storage."""
    global _vault
    _vault = CredentialVault(_default_root())
    return _vault


def reset_credential_vault_for_tests() -> None:
    global _vault
    _vault = None
