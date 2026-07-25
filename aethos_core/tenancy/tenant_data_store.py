# SPDX-License-Identifier: Apache-2.0
"""Tenant-scoped durable data store (Phase 5 — Correction 2).

All tenant-owned state that must not leak across tenants is stored in SQLite with
an enforced ``tenant_id`` filter on every query. Single-tenant mode (default) uses
the operator ``default`` tenant — byte-for-byte equivalent isolation semantics with
one logical owner.

On hosted deploys with ``DATABASE_URL``, records are stored in Postgres so api,
worker, and multiple replicas share the same backing store.

Namespaces partition record keys (e.g. ``conversation_threads`` + session id).
Vector memory uses a dedicated append table for per-entry recall.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

_lock = threading.RLock()
_conn: Any = None
_db_path_cache: Path | None = None
_backend: str | None = None


def _settings() -> Any:
    from aethos_core.config import get_settings

    return get_settings()


def _database_url() -> str:
    return str(
        os.environ.get("DATABASE_URL", "") or os.environ.get("POSTGRES_URL", "") or ""
    ).strip()


def shared_store_backend_label() -> str:
    """``postgres`` | ``tenant_sqlite`` | ``local_sqlite`` — for startup diagnostics."""
    if _database_url():
        return "postgres"
    from aethos_core.production.deployment_mode import is_hosted_deployment

    if is_hosted_deployment():
        return "tenant_sqlite"
    return "local_sqlite"


def _is_postgres() -> bool:
    return _backend == "postgres"


def resolve_data_tenant(tenant_id: str | None = None) -> str:
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
    raw = str(os.environ.get("TENANT_DATA_DIR", "") or "").strip()
    if raw:
        root = Path(raw).resolve()
    else:
        from aethos_core.aethos_identity.identity_contract_loader import repo_root

        root = (repo_root() / "data" / "tenant_data").resolve()
    root.mkdir(parents=True, exist_ok=True)
    _db_path_cache = root / "tenant_data.db"
    return _db_path_cache


def _init_schema(conn: Any) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tenant_records ("
        "tenant_id TEXT NOT NULL, namespace TEXT NOT NULL, record_key TEXT NOT NULL, "
        "payload TEXT NOT NULL, updated_at REAL NOT NULL, "
        "PRIMARY KEY (tenant_id, namespace, record_key))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tenant_vector_entries ("
        "tenant_id TEXT NOT NULL, entry_id TEXT NOT NULL, payload TEXT NOT NULL, "
        "updated_at REAL NOT NULL, PRIMARY KEY (tenant_id, entry_id))"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_vector_tenant ON tenant_vector_entries(tenant_id, updated_at)"
    )
    conn.commit()


def _connect_sqlite() -> sqlite3.Connection:
    global _conn, _backend
    if _conn is not None and _backend == "sqlite":
        return _conn
    conn = sqlite3.connect(str(_db_path()), check_same_thread=False)
    _init_schema(conn)
    _conn = conn
    _backend = "sqlite"
    return conn


def _connect_postgres() -> Any:
    global _conn, _backend
    if _conn is not None and _backend == "postgres":
        return _conn
    import psycopg

    conn = psycopg.connect(_database_url())
    _init_schema(conn)
    _conn = conn
    _backend = "postgres"
    return conn


def _connect() -> Any:
    if _database_url():
        return _connect_postgres()
    return _connect_sqlite()


def _execute(conn: Any, sql_pg: str, sql_sqlite: str, params: tuple[Any, ...]) -> Any:
    if _is_postgres():
        return conn.execute(sql_pg, params)
    return conn.execute(sql_sqlite, params)


def reset_for_tests() -> None:
    global _conn, _db_path_cache, _backend
    with _lock:
        if _conn is not None:
            try:
                _conn.close()
            except Exception:
                pass
        _conn = None
        _backend = None
        _db_path_cache = None


def get_record(
    namespace: str, record_key: str, *, tenant_id: str | None = None, default: Any = None
) -> Any:
    tid = resolve_data_tenant(tenant_id)
    key = (record_key or "").strip()
    if not key:
        return default
    try:
        with _lock:
            conn = _connect()
            row = _execute(
                conn,
                "SELECT payload FROM tenant_records WHERE tenant_id = %s AND namespace = %s AND record_key = %s",
                "SELECT payload FROM tenant_records WHERE tenant_id = ? AND namespace = ? AND record_key = ?",
                (tid, namespace, key),
            ).fetchone()
    except Exception:
        return default
    if not row:
        return default
    try:
        return json.loads(str(row[0]))
    except (json.JSONDecodeError, TypeError):
        return default


def set_record(namespace: str, record_key: str, payload: Any, *, tenant_id: str | None = None) -> None:
    tid = resolve_data_tenant(tenant_id)
    key = (record_key or "").strip()
    if not key:
        return
    body = json.dumps(payload)
    now = time.time()
    with _lock:
        conn = _connect()
        _execute(
            conn,
            "INSERT INTO tenant_records (tenant_id, namespace, record_key, payload, updated_at) "
            "VALUES (%s, %s, %s, %s, %s) "
            "ON CONFLICT(tenant_id, namespace, record_key) DO UPDATE SET "
            "payload = excluded.payload, updated_at = excluded.updated_at",
            "INSERT INTO tenant_records (tenant_id, namespace, record_key, payload, updated_at) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(tenant_id, namespace, record_key) DO UPDATE SET "
            "payload = excluded.payload, updated_at = excluded.updated_at",
            (tid, namespace, key, body, now),
        )
        conn.commit()


def delete_record(namespace: str, record_key: str, *, tenant_id: str | None = None) -> bool:
    tid = resolve_data_tenant(tenant_id)
    key = (record_key or "").strip()
    if not key:
        return False
    with _lock:
        conn = _connect()
        cur = _execute(
            conn,
            "DELETE FROM tenant_records WHERE tenant_id = %s AND namespace = %s AND record_key = %s",
            "DELETE FROM tenant_records WHERE tenant_id = ? AND namespace = ? AND record_key = ?",
            (tid, namespace, key),
        )
        conn.commit()
        return int(cur.rowcount or 0) > 0


def list_vector_entries(*, tenant_id: str | None = None, limit: int = 500) -> list[dict[str, Any]]:
    tid = resolve_data_tenant(tenant_id)
    cap = max(1, limit)
    try:
        with _lock:
            conn = _connect()
            rows = _execute(
                conn,
                "SELECT payload FROM tenant_vector_entries WHERE tenant_id = %s "
                "ORDER BY updated_at ASC LIMIT %s",
                "SELECT payload FROM tenant_vector_entries WHERE tenant_id = ? "
                "ORDER BY updated_at ASC LIMIT ?",
                (tid, cap),
            ).fetchall()
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for (payload,) in rows:
        try:
            row = json.loads(str(payload))
            if isinstance(row, dict):
                out.append(row)
        except (json.JSONDecodeError, TypeError):
            continue
    return out


def append_vector_entry(entry: dict[str, Any], *, tenant_id: str | None = None) -> None:
    tid = resolve_data_tenant(tenant_id)
    entry_id = str(entry.get("id") or "")
    if not entry_id:
        return
    body = json.dumps(entry)
    now = time.time()
    with _lock:
        conn = _connect()
        _execute(
            conn,
            "INSERT INTO tenant_vector_entries (tenant_id, entry_id, payload, updated_at) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT(tenant_id, entry_id) DO UPDATE SET "
            "payload = excluded.payload, updated_at = excluded.updated_at",
            "INSERT INTO tenant_vector_entries (tenant_id, entry_id, payload, updated_at) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(tenant_id, entry_id) DO UPDATE SET "
            "payload = excluded.payload, updated_at = excluded.updated_at",
            (tid, entry_id, body, now),
        )
        _execute(
            conn,
            "DELETE FROM tenant_vector_entries WHERE tenant_id = %s AND entry_id NOT IN ("
            "SELECT entry_id FROM tenant_vector_entries WHERE tenant_id = %s "
            "ORDER BY updated_at DESC LIMIT %s)",
            "DELETE FROM tenant_vector_entries WHERE tenant_id = ? AND entry_id NOT IN ("
            "SELECT entry_id FROM tenant_vector_entries WHERE tenant_id = ? "
            "ORDER BY updated_at DESC LIMIT ?)",
            (tid, tid, 500),
        )
        conn.commit()


def list_records(
    namespace: str, *, tenant_id: str | None = None, limit: int = 40
) -> list[dict[str, Any]]:
    """List records in a namespace for the current tenant (newest first)."""
    tid = resolve_data_tenant(tenant_id)
    cap = max(1, limit)
    try:
        with _lock:
            conn = _connect()
            rows = _execute(
                conn,
                "SELECT record_key, payload FROM tenant_records WHERE tenant_id = %s AND namespace = %s "
                "ORDER BY updated_at DESC LIMIT %s",
                "SELECT record_key, payload FROM tenant_records WHERE tenant_id = ? AND namespace = ? "
                "ORDER BY updated_at DESC LIMIT ?",
                (tid, namespace, cap),
            ).fetchall()
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for record_key, payload in rows:
        try:
            data = json.loads(str(payload))
            if isinstance(data, dict):
                data.setdefault("_record_key", record_key)
                out.append(data)
        except (json.JSONDecodeError, TypeError):
            continue
    return out


def get_record_by_namespace_key(
    namespace: str, record_key: str, *, tenant_id: str | None = None
) -> dict[str, Any] | None:
    data = get_record(namespace, record_key, tenant_id=tenant_id, default=None)
    return data if isinstance(data, dict) else None


def clear_namespace(namespace: str, *, tenant_id: str | None = None) -> None:
    tid = resolve_data_tenant(tenant_id)
    with _lock:
        conn = _connect()
        _execute(
            conn,
            "DELETE FROM tenant_records WHERE tenant_id = %s AND namespace = %s",
            "DELETE FROM tenant_records WHERE tenant_id = ? AND namespace = ?",
            (tid, namespace),
        )
        conn.commit()
