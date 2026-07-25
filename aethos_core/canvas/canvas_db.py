# SPDX-License-Identifier: Apache-2.0
"""Postgres-backed Live Canvas view store — shared across api/worker/replicas."""

from __future__ import annotations

import json
import os
import threading
import time
from typing import Any

_lock = threading.RLock()
_conn: Any = None

_MAX_VIEWS_PER_SESSION = 50


def _database_url() -> str:
    return str(
        os.environ.get("DATABASE_URL", "") or os.environ.get("POSTGRES_URL", "") or ""
    ).strip()


def canvas_uses_postgres() -> bool:
    return bool(_database_url())


def _connect() -> Any:
    global _conn
    if _conn is not None:
        return _conn
    import psycopg

    _conn = psycopg.connect(_database_url())
    return _conn


def reset_canvas_db_for_tests() -> None:
    global _conn
    with _lock:
        if _conn is not None:
            try:
                _conn.close()
            except Exception:
                pass
        _conn = None


def init_canvas_schema() -> None:
    """Idempotent schema bootstrap — safe on api and worker boot."""
    if not canvas_uses_postgres():
        return
    with _lock:
        conn = _connect()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS canvas_views (
                tenant_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                view_id TEXT NOT NULL,
                view_type TEXT NOT NULL,
                title TEXT NOT NULL,
                data JSONB NOT NULL,
                read_only BOOLEAN NOT NULL DEFAULT TRUE,
                created_at DOUBLE PRECISION NOT NULL,
                PRIMARY KEY (tenant_id, session_id, view_id)
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canvas_views_lookup
            ON canvas_views (tenant_id, session_id, created_at DESC)
            """
        )
        conn.commit()


def _resolve_tenant(tenant_id: str | None = None) -> str:
    from aethos_core.tenancy.tenant_data_store import resolve_data_tenant

    return resolve_data_tenant(tenant_id)


def delete_canvas_views_by_type(
    *,
    session_keys: list[str],
    view_type: str,
    tenant_id: str | None = None,
) -> None:
    """Remove prior views of the same type so re-renders replace instead of stack."""
    if not canvas_uses_postgres():
        return
    init_canvas_schema()
    keys = [k for k in session_keys if k]
    if not keys:
        return
    tid = _resolve_tenant(tenant_id)
    vt = (view_type or "").strip().lower()
    with _lock:
        conn = _connect()
        conn.execute(
            """
            DELETE FROM canvas_views
            WHERE tenant_id = %s AND session_id = ANY(%s) AND view_type = %s
            """,
            (tid, keys, vt),
        )
        conn.commit()


def insert_canvas_view(
    *,
    session_keys: list[str],
    view_id: str,
    view_type: str,
    title: str,
    data: Any,
    tenant_id: str | None = None,
) -> None:
    if not canvas_uses_postgres():
        return
    init_canvas_schema()
    tid = _resolve_tenant(tenant_id)
    now = time.time()
    payload = json.dumps(data if data is not None else {})
    with _lock:
        conn = _connect()
        for sid in session_keys:
            if not sid:
                continue
            conn.execute(
                """
                INSERT INTO canvas_views (
                    tenant_id, session_id, view_id, view_type, title, data, read_only, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s)
                ON CONFLICT (tenant_id, session_id, view_id) DO UPDATE SET
                    view_type = EXCLUDED.view_type,
                    title = EXCLUDED.title,
                    data = EXCLUDED.data,
                    read_only = EXCLUDED.read_only,
                    created_at = EXCLUDED.created_at
                """,
                (tid, sid, view_id, view_type, title, payload, True, now),
            )
            conn.execute(
                """
                DELETE FROM canvas_views
                WHERE tenant_id = %s AND session_id = %s AND view_id NOT IN (
                    SELECT view_id FROM canvas_views
                    WHERE tenant_id = %s AND session_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                )
                """,
                (tid, sid, tid, sid, _MAX_VIEWS_PER_SESSION),
            )
        conn.commit()


def list_canvas_views(
    *,
    session_keys: list[str],
    tenant_id: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    if not canvas_uses_postgres():
        return []
    init_canvas_schema()
    keys = [k for k in session_keys if k]
    if not keys:
        return []
    tid = _resolve_tenant(tenant_id)
    cap = max(1, min(int(limit or 50), _MAX_VIEWS_PER_SESSION))
    with _lock:
        conn = _connect()
        rows = conn.execute(
            """
            SELECT view_id, view_type, title, data, read_only, created_at, session_id
            FROM canvas_views
            WHERE tenant_id = %s AND session_id = ANY(%s)
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (tid, keys, cap * len(keys)),
        ).fetchall()
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for view_id, view_type, title, data, read_only, created_at, session_id in rows:
        vid = str(view_id or "")
        if vid and vid in seen:
            continue
        if vid:
            seen.add(vid)
        payload = data
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {}
        out.append(
            {
                "id": vid,
                "view_type": str(view_type or ""),
                "title": str(title or ""),
                "data": payload,
                "read_only": bool(read_only),
                "created_at": float(created_at or 0),
                "_session_id": str(session_id or ""),
            }
        )
    out.sort(key=lambda v: float(v.get("created_at") or 0), reverse=True)
    return out[:cap]


def latest_canvas_session_for_tenant(*, tenant_id: str | None = None) -> str:
    """Session id of the most recently rendered view for this tenant (across all sessions).

    Lets the Canvas auto-show the latest render even when the panel is bound to a
    different session id than the chat used (cross-window/browser)."""
    if not canvas_uses_postgres():
        return ""
    init_canvas_schema()
    tid = _resolve_tenant(tenant_id)
    with _lock:
        conn = _connect()
        row = conn.execute(
            """
            SELECT session_id FROM canvas_views
            WHERE tenant_id = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (tid,),
        ).fetchone()
    return str(row[0]) if row and row[0] else ""


def clear_canvas_views_for_tests(tenant_id: str | None = None) -> None:
    if not canvas_uses_postgres():
        return
    init_canvas_schema()
    tid = _resolve_tenant(tenant_id)
    with _lock:
        conn = _connect()
        conn.execute("DELETE FROM canvas_views WHERE tenant_id = %s", (tid,))
        conn.commit()
