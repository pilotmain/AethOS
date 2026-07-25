# SPDX-License-Identifier: Apache-2.0
"""Server-persisted chat threads keyed by tenant + session_id."""

from __future__ import annotations

import json
import re
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

_MAX_THREADS = 40
_MAX_MESSAGES = 80
_SESSION_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def _sanitize_session_id(session_id: str) -> str:
    raw = (session_id or "default").strip()[:64]
    cleaned = _SESSION_RE.sub("-", raw).strip("-")
    return cleaned or "default"


def _tenant_id() -> str:
    from aethos_core.tenancy import get_current_tenant

    tenant = str(get_current_tenant() or "default").strip().lower()
    safe = _SESSION_RE.sub("-", tenant).strip("-")[:120]
    return safe or "default"


def _root_base() -> Path:
    return Path("data/conversation/chat_threads").expanduser()


def _tenant_root() -> Path:
    root = _root_base() / _tenant_id()
    root.mkdir(parents=True, exist_ok=True)
    _migrate_legacy_index_if_needed(root)
    return root


def _migrate_legacy_index_if_needed(tenant_root: Path) -> None:
    """Single-tenant legacy index.json → per-tenant layout (default tenant only)."""
    if _tenant_id() != "default":
        return
    legacy = _root_base() / "index.json"
    new_index = tenant_root / "index.json"
    if legacy.is_file() and not new_index.is_file():
        try:
            tenant_root.mkdir(parents=True, exist_ok=True)
            legacy.replace(new_index)
        except OSError:
            pass


def _index_path() -> Path:
    return _tenant_root() / "index.json"


def _load_index() -> dict[str, Any]:
    path = _index_path()
    if not path.is_file():
        return {"threads": {}, "order": []}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            raw.setdefault("threads", {})
            raw.setdefault("order", [])
            return raw
    except (OSError, json.JSONDecodeError):
        pass
    return {"threads": {}, "order": []}


def _save_index(data: dict[str, Any]) -> None:
    data["updated_at"] = time()
    _index_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def _trim_messages(messages: list[Any]) -> list[Any]:
    if not isinstance(messages, list):
        return []
    rows = [row for row in messages if isinstance(row, dict)]
    return rows[-_MAX_MESSAGES:]


def list_chat_threads(*, limit: int = _MAX_THREADS) -> dict[str, Any]:
    data = _load_index()
    threads: dict[str, Any] = data.get("threads") or {}
    order: list[str] = list(data.get("order") or [])
    cap = max(1, min(limit, _MAX_THREADS))
    rows: list[dict[str, Any]] = []
    for sid in order:
        row = threads.get(sid)
        if not isinstance(row, dict):
            continue
        messages = row.get("messages") or []
        rows.append(
            {
                "session_id": sid,
                "title": str(row.get("title") or "New chat"),
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at"),
                "message_count": len(messages) if isinstance(messages, list) else 0,
            }
        )
        if len(rows) >= cap:
            break
    return {"ok": True, "threads": rows, "count": len(rows), "tenant_id": _tenant_id()}


def get_chat_thread(session_id: str) -> dict[str, Any] | None:
    sid = _sanitize_session_id(session_id)
    data = _load_index()
    row = (data.get("threads") or {}).get(sid)
    if not isinstance(row, dict):
        return None
    return {
        "ok": True,
        "thread": {
            "session_id": sid,
            "title": str(row.get("title") or "New chat"),
            "messages": _trim_messages(list(row.get("messages") or [])),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
        },
        "tenant_id": _tenant_id(),
    }


def create_chat_thread(*, title: str | None = None, session_id: str | None = None) -> dict[str, Any]:
    sid = _sanitize_session_id(session_id or f"sess-{uuid4().hex[:10]}")
    now = time()
    data = _load_index()
    threads: dict[str, Any] = dict(data.get("threads") or {})
    order: list[str] = list(data.get("order") or [])
    if sid not in threads:
        threads[sid] = {
            "session_id": sid,
            "title": (title or "New chat").strip()[:120] or "New chat",
            "messages": [],
            "created_at": now,
            "updated_at": now,
        }
        order = [sid] + [s for s in order if s != sid]
    data["threads"] = threads
    data["order"] = order[:_MAX_THREADS]
    _save_index(data)
    return get_chat_thread(sid) or {"ok": False, "error": "create_failed"}


def upsert_chat_thread(
    *,
    session_id: str,
    title: str | None = None,
    messages: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    sid = _sanitize_session_id(session_id)
    now = time()
    data = _load_index()
    threads: dict[str, Any] = dict(data.get("threads") or {})
    order: list[str] = list(data.get("order") or [])
    existing = threads.get(sid) if isinstance(threads.get(sid), dict) else {}
    created_at = existing.get("created_at") or now
    next_title = (title or existing.get("title") or "New chat").strip()[:120] or "New chat"
    next_messages = _trim_messages(messages if messages is not None else list(existing.get("messages") or []))
    threads[sid] = {
        "session_id": sid,
        "title": next_title,
        "messages": next_messages,
        "created_at": created_at,
        "updated_at": now,
    }
    order = [sid] + [s for s in order if s != sid]
    data["threads"] = threads
    data["order"] = order[:_MAX_THREADS]
    _save_index(data)
    return get_chat_thread(sid) or {"ok": False, "error": "upsert_failed"}


def delete_chat_thread(session_id: str) -> dict[str, Any]:
    sid = _sanitize_session_id(session_id)
    data = _load_index()
    threads: dict[str, Any] = dict(data.get("threads") or {})
    order: list[str] = list(data.get("order") or [])
    if sid not in threads:
        return {"ok": False, "error": "not_found"}
    del threads[sid]
    order = [s for s in order if s != sid]
    data["threads"] = threads
    data["order"] = order
    _save_index(data)
    return {"ok": True, "deleted_session_id": sid, "tenant_id": _tenant_id()}
