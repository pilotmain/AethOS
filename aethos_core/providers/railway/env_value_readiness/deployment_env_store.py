# SPDX-License-Identifier: Apache-2.0
"""Encrypted per-target deployment env values — secure_store_reference resolution."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.providers.railway.env_value_readiness.env_value_inventory import (
    _deployment_env_presence_path,
    _load_deployment_env_presence,
)


def _tenant_data_segment() -> str:
    from aethos_core.tenancy.tenant_data_store import resolve_data_tenant

    return resolve_data_tenant()


def _values_root() -> Path:
    root = (
        Path(__file__).resolve().parents[3]
        / "data"
        / "deployment_env_values"
        / _tenant_data_segment()
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_target_key(target_key: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_|.-]+", "_", (target_key or "").strip())[:180]


def _values_path(target_key: str) -> Path:
    return _values_root() / f"{_safe_target_key(target_key)}.json"


def _encrypt_value(value: str) -> str:
    from aethos_core.security.credential_vault import _encrypt

    return _encrypt(str(value or "").encode("utf-8")).decode("ascii")


def _decrypt_value(token: str) -> str:
    from aethos_core.security.credential_vault import _decrypt

    return _decrypt(str(token or "").encode("ascii")).decode("utf-8")


def _load_values_blob(target_key: str) -> dict[str, str]:
    path = _values_path(target_key)
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    values = raw.get("values") if isinstance(raw, dict) else None
    if not isinstance(values, dict):
        return {}
    return {str(k).strip().upper(): str(v) for k, v in values.items() if str(k).strip()}


def _persist_values_blob(target_key: str, values: dict[str, str]) -> None:
    path = _values_path(target_key)
    path.write_text(
        json.dumps(
            {
                "target_key": target_key,
                "values": dict(values),
                "updated_at": datetime.now(UTC).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _mark_presence(target_key: str, present_names: set[str]) -> None:
    path = _deployment_env_presence_path(target_key)
    path.write_text(
        json.dumps(
            {
                "present_names": sorted(present_names),
                "updated_at": datetime.now(UTC).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def register_deployment_env_value(*, target_key: str, name: str, value: str) -> None:
    """Store one deployment env value encrypted and mark presence (never log value)."""
    upper = (name or "").strip().upper()
    cleaned = str(value or "").strip()
    if not upper or not cleaned:
        raise ValueError("Env name and value are required.")
    blob = _load_values_blob(target_key)
    blob[upper] = _encrypt_value(cleaned)
    _persist_values_blob(target_key, blob)
    present = _load_deployment_env_presence(target_key)
    present.add(upper)
    _mark_presence(target_key, present)


def register_deployment_env_values(*, target_key: str, values: dict[str, str]) -> list[str]:
    """Store multiple env values; returns registered names (never values)."""
    registered: list[str] = []
    for raw_name, raw_value in (values or {}).items():
        name = str(raw_name or "").strip()
        value = str(raw_value or "").strip()
        if not name or not value:
            continue
        register_deployment_env_value(target_key=target_key, name=name, value=value)
        registered.append(name.strip().upper())
    return registered


def resolve_deployment_env_value(*, target_key: str, name: str) -> str | None:
    """Resolve one deployment env value from encrypted store."""
    upper = (name or "").strip().upper()
    if not upper:
        return None
    token = _load_values_blob(target_key).get(upper)
    if not token:
        return None
    try:
        value = _decrypt_value(token).strip()
    except Exception:
        return None
    return value or None


def list_deployment_env_value_names(*, target_key: str) -> list[str]:
    return sorted(_load_values_blob(target_key).keys())


def clear_deployment_env_store_for_tests() -> None:
    base = Path(__file__).resolve().parents[3] / "data" / "deployment_env_values"
    if base.is_dir():
        for path in base.rglob("*.json"):
            path.unlink()


def deployment_env_store_diagnostics(*, target_key: str) -> dict[str, Any]:
    names = list_deployment_env_value_names(target_key=target_key)
    return {
        "target_key": target_key,
        "stored_name_count": len(names),
        "stored_names": names,
        "presence_names": sorted(_load_deployment_env_presence(target_key)),
    }
