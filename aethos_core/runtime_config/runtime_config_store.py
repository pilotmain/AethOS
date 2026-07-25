# SPDX-License-Identifier: Apache-2.0
"""SQLite-backed runtime configuration store (canonical, UI-writable).

Holds allowlisted, non-secret config values set by the user from Mission Control.
Values are stored as strings (typed on read by the resolver). Cached in-memory with
explicit invalidation on write, so hot-path reads never touch disk.

Multi-tenant (Phase 3): each row is keyed by ``(tenant_id, key)``. In single-tenant
mode every read/write uses the operator/default tenant so behavior is unchanged.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

_lock = threading.RLock()
_conn: sqlite3.Connection | None = None
_db_path_cache: Path | None = None
# tenant_id -> {key: value}
_value_cache: dict[str, dict[str, str]] | None = None


def _settings() -> Any:
    from aethos_core.config import get_settings

    return get_settings()


def _resolve_tenant(tenant_id: str | None) -> str:
    if tenant_id is not None:
        from aethos_core.tenancy import normalize_tenant

        return normalize_tenant(tenant_id)
    from aethos_core.tenancy import DEFAULT_TENANT, get_current_tenant

    if not _settings().multi_tenant_enabled:
        return DEFAULT_TENANT
    return get_current_tenant()


def _db_path() -> Path:
    global _db_path_cache
    if _db_path_cache is not None:
        return _db_path_cache
    from aethos_core.aethos_identity.identity_contract_loader import repo_root

    raw = str(getattr(_settings(), "runtime_config_dir", "data/runtime_config") or "data/runtime_config")
    base = Path(raw)
    root = base if base.is_absolute() else (repo_root() / base)
    root.mkdir(parents=True, exist_ok=True)
    _db_path_cache = (root / "runtime_config.db").resolve()
    return _db_path_cache


def _migrate_schema(conn: sqlite3.Connection) -> None:
    """Upgrade legacy key-only table to (tenant_id, key) composite PK."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(runtime_config)").fetchall()}
    if not cols:
        conn.execute(
            "CREATE TABLE runtime_config ("
            "tenant_id TEXT NOT NULL DEFAULT 'default', "
            "key TEXT NOT NULL, "
            "value TEXT NOT NULL, "
            "updated_at REAL NOT NULL, "
            "PRIMARY KEY (tenant_id, key))"
        )
        conn.commit()
        return
    if "tenant_id" in cols:
        return
    conn.execute(
        "CREATE TABLE runtime_config_v2 ("
        "tenant_id TEXT NOT NULL DEFAULT 'default', "
        "key TEXT NOT NULL, "
        "value TEXT NOT NULL, "
        "updated_at REAL NOT NULL, "
        "PRIMARY KEY (tenant_id, key))"
    )
    conn.execute(
        "INSERT INTO runtime_config_v2 (tenant_id, key, value, updated_at) "
        "SELECT 'default', key, value, updated_at FROM runtime_config"
    )
    conn.execute("DROP TABLE runtime_config")
    conn.execute("ALTER TABLE runtime_config_v2 RENAME TO runtime_config")
    conn.commit()


def _connect() -> sqlite3.Connection:
    global _conn
    if _conn is not None:
        return _conn
    conn = sqlite3.connect(str(_db_path()), check_same_thread=False)
    _migrate_schema(conn)
    _conn = conn
    return conn


def reset_for_tests() -> None:
    global _conn, _db_path_cache, _value_cache
    with _lock:
        if _conn is not None:
            try:
                _conn.close()
            except Exception:
                pass
        _conn = None
        _db_path_cache = None
        _value_cache = None


def _load_all(tenant_id: str | None = None) -> dict[str, str]:
    global _value_cache
    tid = _resolve_tenant(tenant_id)
    if _value_cache is not None and tid in _value_cache:
        return _value_cache[tid]
    values: dict[str, str] = {}
    try:
        with _lock:
            conn = _connect()
            for key, value in conn.execute(
                "SELECT key, value FROM runtime_config WHERE tenant_id = ?", (tid,)
            ).fetchall():
                values[str(key)] = str(value)
    except Exception:
        values = {}
    if _value_cache is None:
        _value_cache = {}
    _value_cache[tid] = values
    return values


def all_runtime_values(*, tenant_id: str | None = None) -> dict[str, str]:
    return dict(_load_all(tenant_id))


def get_runtime_value(key: str, *, tenant_id: str | None = None) -> str | None:
    return _load_all(tenant_id).get((key or "").strip())


def set_runtime_value(key: str, value: str, *, tenant_id: str | None = None) -> None:
    global _value_cache
    k = (key or "").strip()
    if not k:
        return
    tid = _resolve_tenant(tenant_id)
    with _lock:
        conn = _connect()
        conn.execute(
            "INSERT INTO runtime_config (tenant_id, key, value, updated_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(tenant_id, key) DO UPDATE SET "
            "value = excluded.value, updated_at = excluded.updated_at",
            (tid, k, str(value), time.time()),
        )
        conn.commit()
        if _value_cache is not None:
            _value_cache.pop(tid, None)


def delete_runtime_value(key: str, *, tenant_id: str | None = None) -> bool:
    global _value_cache
    k = (key or "").strip()
    if not k:
        return False
    tid = _resolve_tenant(tenant_id)
    with _lock:
        conn = _connect()
        cur = conn.execute(
            "DELETE FROM runtime_config WHERE tenant_id = ? AND key = ?", (tid, k)
        )
        conn.commit()
        if _value_cache is not None:
            _value_cache.pop(tid, None)
        return cur.rowcount > 0
