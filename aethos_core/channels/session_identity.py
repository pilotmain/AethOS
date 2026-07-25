# SPDX-License-Identifier: Apache-2.0
"""Unified session identity — map session IDs to channel transports."""

from __future__ import annotations

from aethos_core.channels.telegram.telegram_identity import is_telegram_session, telegram_session_id

__all__ = [
    "external_chat_id_from_session",
    "is_telegram_session",
    "parse_session_channel",
    "telegram_session_id",
    "web_session_id",
]

_CHANNEL_PREFIXES: tuple[tuple[str, str], ...] = (
    ("tg-", "telegram"),
    ("slack-", "slack"),
    ("discord-", "discord"),
    ("email-", "email"),
    ("sms-", "sms"),
    ("voice-", "voice"),
)


def parse_session_channel(session_id: str) -> str:
    """Infer transport channel from session id prefix."""
    sid = (session_id or "").strip()
    if not sid:
        return "web"
    lower = sid.lower()
    for prefix, channel in _CHANNEL_PREFIXES:
        if lower.startswith(prefix):
            return channel
    return "web"


def external_chat_id_from_session(session_id: str) -> str | None:
    """Extract provider-native chat/thread id when encoded in session id."""
    sid = (session_id or "").strip()
    if is_telegram_session(sid):
        parts = sid.split("-", 2)
        if len(parts) >= 2 and parts[1]:
            return parts[1]
    for prefix, _channel in _CHANNEL_PREFIXES:
        if sid.lower().startswith(prefix):
            remainder = sid[len(prefix) :]
            chat = remainder.split("-", 1)[0]
            return chat or None
    return None


def web_session_id(session_key: str = "default") -> str:
    key = (session_key or "default").strip() or "default"
    return f"web-{key}"[:64]
