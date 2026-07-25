# SPDX-License-Identifier: Apache-2.0
"""Map Telegram users/chats to AethOS session IDs."""

from __future__ import annotations


def telegram_session_id(*, chat_id: str | int, user_id: str | int | None = None) -> str:
    """Stable session id for orchestration — fits job/chat 64-char limit."""
    cid = str(chat_id).strip()
    if user_id is not None:
        uid = str(user_id).strip()
        return f"tg-{cid}-{uid}"[:64]
    return f"tg-{cid}"[:64]


def is_telegram_session(session_id: str) -> bool:
    return (session_id or "").startswith("tg-")
