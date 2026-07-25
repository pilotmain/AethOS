# SPDX-License-Identifier: Apache-2.0
"""Canonical credential vault paths — single source of truth."""

from __future__ import annotations

from pathlib import Path

_INDEX_FILENAME = "credentials.json"
_SECRET_DIRNAME = "secrets"
_MACHINE_KEY_FILENAME = ".vault_key"
_HYDRATION_REPORT = "hydration_report.json"
_AUDIT_FILENAME = "credential_audit.jsonl"


def resolve_credential_root() -> Path:
    from aethos_core.config import get_settings

    raw = Path(get_settings().credentials_dir)
    if raw.is_absolute():
        root = raw
    else:
        repo_root = Path(__file__).resolve().parents[2]
        root = repo_root / raw
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def credential_root() -> Path:
    return resolve_credential_root()


def credential_metadata_dir() -> Path:
    root = credential_root()
    root.mkdir(parents=True, exist_ok=True)
    return root


def credential_secret_dir() -> Path:
    path = credential_root() / _SECRET_DIRNAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def credential_audit_dir() -> Path:
    return credential_metadata_dir()


def credential_index_path() -> Path:
    return credential_metadata_dir() / _INDEX_FILENAME


def credential_secret_path(credential_id: str) -> Path:
    return credential_secret_dir() / f"{credential_id}.enc"


def credential_audit_path() -> Path:
    return credential_audit_dir() / _AUDIT_FILENAME


def hydration_report_path() -> Path:
    return credential_metadata_dir() / _HYDRATION_REPORT


def machine_key_path() -> Path:
    """Fernet key — sibling data/secrets (stable across credential root resolution)."""
    path = credential_root().parent / "secrets" / _MACHINE_KEY_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
