# SPDX-License-Identifier: Apache-2.0
"""In-memory Telegram activity — no message content stored."""

from __future__ import annotations

from time import time
from typing import Any

_last_in_at: float | None = None
_last_out_at: float | None = None
_active_chats: set[str] = set()
_sessions: dict[str, dict[str, Any]] = {}
_last_send_ok: bool | None = None
_last_send_error: str | None = None
_outbound_success_count = 0
_outbound_fail_count = 0


def _mask_id(value: str) -> str:
    raw = str(value or "")
    if len(raw) <= 4:
        return "****"
    return f"{raw[:2]}…{raw[-2:]}"


def record_inbound(
    *,
    chat_id: str,
    user_id: str = "",
    session_id: str = "",
    preview: str = "",
) -> None:
    global _last_in_at
    now = time()
    _last_in_at = now
    if chat_id:
        _active_chats.add(chat_id)
    sid = session_id or (f"tg-{chat_id}-{user_id}" if chat_id and user_id else "")
    if sid:
        entry = _sessions.setdefault(
            sid,
            {
                "session_id": sid,
                "chat_id_masked": _mask_id(chat_id),
                "user_id_masked": _mask_id(user_id),
            },
        )
        entry["last_received_at"] = now
        if preview:
            entry["last_message_preview"] = preview[:120]


def record_outbound(*, chat_id: str, session_id: str = "", ok: bool = True, error: str = "") -> None:
    global _last_out_at, _last_send_ok, _last_send_error, _outbound_success_count, _outbound_fail_count
    now = time()
    _last_out_at = now
    _last_send_ok = ok
    _last_send_error = error[:200] if error and not ok else None
    if ok:
        _outbound_success_count += 1
    else:
        _outbound_fail_count += 1
    if chat_id:
        _active_chats.add(chat_id)
    sid = session_id or (f"tg-{chat_id}" if chat_id else "")
    if sid and sid in _sessions:
        _sessions[sid]["last_sent_at"] = now


def record_session_operation(*, session_id: str, operation: str) -> None:
    if not session_id:
        return
    entry = _sessions.setdefault(session_id, {"session_id": session_id})
    entry["last_operation"] = operation[:120]
    entry["last_operation_at"] = time()


def activity_snapshot() -> dict[str, float | int | bool | str | None]:
    return {
        "last_received_at": _last_in_at,
        "last_sent_at": _last_out_at,
        "active_chats_count": len(_active_chats),
        "last_send_ok": _last_send_ok,
        "last_send_error": _last_send_error,
        "outbound_success_count": _outbound_success_count,
        "outbound_fail_count": _outbound_fail_count,
    }


def list_sessions(*, limit: int = 20) -> list[dict[str, Any]]:
    rows = list(_sessions.values())
    rows.sort(key=lambda r: float(r.get("last_received_at") or r.get("last_sent_at") or 0), reverse=True)
    return rows[:limit]


def clear_for_tests() -> None:
    global _last_in_at, _last_out_at, _last_send_ok, _last_send_error
    global _outbound_success_count, _outbound_fail_count
    _last_in_at = None
    _last_out_at = None
    _last_send_ok = None
    _last_send_error = None
    _outbound_success_count = 0
    _outbound_fail_count = 0
    _active_chats.clear()
    _sessions.clear()
