# SPDX-License-Identifier: Apache-2.0
"""Conversation summary memory — the MEMORY.md "Conversation summary memory" layer.

A rolling, compressed, per-session recap of the conversation (topics, intents,
what was done) so prompts like "what did we discuss / do this hour?" answer from
real history — not the operational-thread-only path. SQLite is the canonical
store. Session-scoped; secrets are redacted before storage; never stores tokens.

Deterministic + incremental: each turn appends one compressed line to the rolling
summary (capped) and a recent-turn row (capped). No LLM call is required to
maintain it, so it is cheap and always available. When VECTOR_MEMORY_ENABLED is
on, the summary is also embedded for optional long-term cross-session recall.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

_lock = threading.Lock()
_conn: sqlite3.Connection | None = None
_db_path_cache: Path | None = None


def _settings() -> Any:
    from aethos_core.config import get_settings

    return get_settings()


def conversation_memory_enabled() -> bool:
    return bool(getattr(_settings(), "conversation_memory_enabled", True))


def _db_path() -> Path:
    global _db_path_cache
    if _db_path_cache is not None:
        return _db_path_cache
    from aethos_core.aethos_identity.identity_contract_loader import repo_root

    raw = str(getattr(_settings(), "conversation_memory_dir", "data/conversation_memory") or "data/conversation_memory")
    base = Path(raw)
    root = base if base.is_absolute() else (repo_root() / base)
    root.mkdir(parents=True, exist_ok=True)
    _db_path_cache = (root / "conversation_memory.db").resolve()
    return _db_path_cache


def _tenant_id() -> str:
    from aethos_core.tenancy.tenant_data_store import resolve_data_tenant

    return resolve_data_tenant()


def _migrate_tenant_schema(conn: sqlite3.Connection) -> None:
    """Add tenant_id to legacy tables (rows migrate to the default tenant)."""
    turn_cols = {row[1] for row in conn.execute("PRAGMA table_info(conversation_turns)").fetchall()}
    if turn_cols and "tenant_id" not in turn_cols:
        conn.execute(
            "CREATE TABLE conversation_turns_v2 ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id TEXT NOT NULL DEFAULT 'default', "
            "session_id TEXT NOT NULL, ts REAL NOT NULL, intent TEXT, user_text TEXT, reply_preview TEXT)"
        )
        conn.execute(
            "INSERT INTO conversation_turns_v2 (id, tenant_id, session_id, ts, intent, user_text, reply_preview) "
            "SELECT id, 'default', session_id, ts, intent, user_text, reply_preview FROM conversation_turns"
        )
        conn.execute("DROP TABLE conversation_turns")
        conn.execute("ALTER TABLE conversation_turns_v2 RENAME TO conversation_turns")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_turns_tenant_session_ts "
            "ON conversation_turns(tenant_id, session_id, ts)"
        )
    elif not turn_cols:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS conversation_turns ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id TEXT NOT NULL DEFAULT 'default', "
            "session_id TEXT NOT NULL, ts REAL NOT NULL, intent TEXT, user_text TEXT, reply_preview TEXT)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_turns_tenant_session_ts "
            "ON conversation_turns(tenant_id, session_id, ts)"
        )

    sum_cols = {row[1] for row in conn.execute("PRAGMA table_info(conversation_summary)").fetchall()}
    if sum_cols and "tenant_id" not in sum_cols:
        conn.execute(
            "CREATE TABLE conversation_summary_v2 ("
            "tenant_id TEXT NOT NULL DEFAULT 'default', session_id TEXT NOT NULL, "
            "summary TEXT, turn_count INTEGER DEFAULT 0, updated_at REAL, "
            "PRIMARY KEY (tenant_id, session_id))"
        )
        conn.execute(
            "INSERT INTO conversation_summary_v2 (tenant_id, session_id, summary, turn_count, updated_at) "
            "SELECT 'default', session_id, summary, turn_count, updated_at FROM conversation_summary"
        )
        conn.execute("DROP TABLE conversation_summary")
        conn.execute("ALTER TABLE conversation_summary_v2 RENAME TO conversation_summary")
    elif not sum_cols:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS conversation_summary ("
            "tenant_id TEXT NOT NULL DEFAULT 'default', session_id TEXT NOT NULL, "
            "summary TEXT, turn_count INTEGER DEFAULT 0, updated_at REAL, "
            "PRIMARY KEY (tenant_id, session_id))"
        )


def _connect() -> sqlite3.Connection:
    global _conn
    if _conn is not None:
        return _conn
    conn = sqlite3.connect(str(_db_path()), check_same_thread=False)
    _migrate_tenant_schema(conn)
    conn.commit()
    _conn = conn
    return conn


def reset_for_tests() -> None:
    global _conn, _db_path_cache
    with _lock:
        if _conn is not None:
            try:
                _conn.close()
            except Exception:
                pass
        _conn = None
        _db_path_cache = None


def _redact(text: str, limit: int) -> str:
    from aethos_core.security.secret_redaction import redact_text

    cleaned = " ".join(str(text or "").split())
    cleaned = redact_text(cleaned)
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 1] + "…"


# Recap/identity meta-prompts and their replies should not pollute the history —
# recording them would make "what did we discuss" recurse on itself.
def _is_recordable(user_text: str, intent: str) -> bool:
    raw = (user_text or "").strip()
    if not raw:
        return False
    skip_intents = {
        "continuity_session_recall",
        "continuity_service_recall",
        "conversation_recap",
        "soul_identity",
    }
    return intent not in skip_intents


def record_turn(*, session_id: str, user_text: str, reply: str, intent: str = "") -> None:
    """Append a turn and fold it into the rolling per-session summary. Best-effort."""
    if not conversation_memory_enabled():
        return
    if not _is_recordable(user_text, intent):
        return
    sid = (session_id or "default").strip() or "default"
    tid = _tenant_id()
    user_preview = _redact(user_text, 400)
    reply_preview = _redact(reply, 240)
    if not user_preview:
        return
    ts = time.time()
    try:
        with _lock:
            conn = _connect()
            conn.execute(
                "INSERT INTO conversation_turns (tenant_id, session_id, ts, intent, user_text, reply_preview) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (tid, sid, ts, intent or "", user_preview, reply_preview),
            )
            _prune_turns(conn, tid, sid)
            _update_summary(conn, tid, sid, ts=ts, user_preview=user_preview, intent=intent)
            conn.commit()
    except Exception:
        return
    _maybe_embed_summary(sid)


def _prune_turns(conn: sqlite3.Connection, tenant_id: str, session_id: str) -> None:
    max_turns = max(10, int(getattr(_settings(), "conversation_memory_max_turns", 80) or 80))
    conn.execute(
        "DELETE FROM conversation_turns WHERE tenant_id = ? AND session_id = ? AND id NOT IN ("
        "SELECT id FROM conversation_turns WHERE tenant_id = ? AND session_id = ? "
        "ORDER BY ts DESC LIMIT ?)",
        (tenant_id, session_id, tenant_id, session_id, max_turns),
    )
    days = int(getattr(_settings(), "retention_chat_days", 0) or 0)
    if getattr(_settings(), "retention_enabled", False) and days > 0:
        cutoff = time.time() - days * 86400
        conn.execute(
            "DELETE FROM conversation_turns WHERE tenant_id = ? AND session_id = ? AND ts < ?",
            (tenant_id, session_id, cutoff),
        )


def _summary_line(ts: float, user_preview: str, intent: str) -> str:
    stamp = datetime.fromtimestamp(ts).strftime("%H:%M")
    label = (intent or "discussed").replace("_", " ")
    return f"- {stamp} · {label}: {user_preview[:160]}"


def _update_summary(
    conn: sqlite3.Connection, tenant_id: str, session_id: str, *, ts: float, user_preview: str, intent: str
) -> None:
    row = conn.execute(
        "SELECT summary, turn_count FROM conversation_summary WHERE tenant_id = ? AND session_id = ?",
        (tenant_id, session_id),
    ).fetchone()
    existing = str(row[0]) if row and row[0] else ""
    count = int(row[1]) if row and row[1] is not None else 0
    line = _summary_line(ts, user_preview, intent)
    summary = (existing + "\n" + line).strip() if existing else line
    cap = max(800, int(getattr(_settings(), "conversation_memory_max_summary_chars", 4000) or 4000))
    if len(summary) > cap:
        # Drop oldest lines until under the cap (rolling compression).
        lines = summary.split("\n")
        while lines and len("\n".join(lines)) > cap:
            lines.pop(0)
        summary = "\n".join(lines)
    conn.execute(
        "INSERT INTO conversation_summary (tenant_id, session_id, summary, turn_count, updated_at) "
        "VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(tenant_id, session_id) DO UPDATE SET summary = excluded.summary, "
        "turn_count = excluded.turn_count, updated_at = excluded.updated_at",
        (tenant_id, session_id, summary, count + 1, ts),
    )


def _maybe_embed_summary(session_id: str) -> None:
    if not getattr(_settings(), "vector_memory_enabled", False):
        return
    try:
        recap = get_session_summary(session_id)
        if not recap.get("summary"):
            return
        from aethos_core.memory.vector_store import remember

        remember(
            text=f"Conversation summary ({session_id}):\n{recap['summary']}",
            tags=["conversation_summary", session_id],
            metadata={"session_id": session_id, "kind": "conversation_summary"},
        )
    except Exception:
        return


def get_session_summary(session_id: str) -> dict[str, Any]:
    sid = (session_id or "default").strip() or "default"
    tid = _tenant_id()
    if not conversation_memory_enabled():
        return {"summary": "", "turn_count": 0}
    try:
        with _lock:
            conn = _connect()
            row = conn.execute(
                "SELECT summary, turn_count, updated_at FROM conversation_summary "
                "WHERE tenant_id = ? AND session_id = ?",
                (tid, sid),
            ).fetchone()
    except Exception:
        return {"summary": "", "turn_count": 0}
    if not row:
        return {"summary": "", "turn_count": 0}
    return {"summary": str(row[0] or ""), "turn_count": int(row[1] or 0), "updated_at": row[2]}


def get_recent_turns(session_id: str, *, hours: float | None = None, limit: int = 40) -> list[dict[str, Any]]:
    sid = (session_id or "default").strip() or "default"
    tid = _tenant_id()
    if not conversation_memory_enabled():
        return []
    try:
        with _lock:
            conn = _connect()
            if hours is not None and hours > 0:
                cutoff = time.time() - hours * 3600
                rows = conn.execute(
                    "SELECT ts, intent, user_text, reply_preview FROM conversation_turns "
                    "WHERE tenant_id = ? AND session_id = ? AND ts >= ? ORDER BY ts ASC LIMIT ?",
                    (tid, sid, cutoff, max(1, limit)),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT ts, intent, user_text, reply_preview FROM conversation_turns "
                    "WHERE tenant_id = ? AND session_id = ? ORDER BY ts DESC LIMIT ?",
                    (tid, sid, max(1, limit)),
                ).fetchall()
                rows = list(reversed(rows))
    except Exception:
        return []
    return [
        {"ts": r[0], "intent": r[1] or "", "user_text": r[2] or "", "reply_preview": r[3] or ""}
        for r in rows
    ]


def compose_conversation_recap_text(session_id: str, *, hours: float | None = None) -> str | None:
    """A human-readable recap of the conversation from stored history, or None."""
    if not conversation_memory_enabled():
        return None
    turns = get_recent_turns(session_id, hours=hours, limit=30)
    if not turns:
        return None
    window = "the last hour" if (hours and hours <= 1.5) else "this session"
    lines = [f"Here's what we covered in {window}:", ""]
    for t in turns:
        stamp = datetime.fromtimestamp(float(t["ts"])).strftime("%H:%M")
        topic = str(t["user_text"])[:160]
        label = str(t["intent"] or "").replace("_", " ")
        prefix = f"`{stamp}`"
        lines.append(f"- {prefix} {topic}" + (f"  _( {label} )_" if label else ""))
    return "\n".join(lines)
