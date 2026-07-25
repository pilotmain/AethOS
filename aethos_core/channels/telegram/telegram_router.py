# SPDX-License-Identifier: Apache-2.0
"""Route Telegram messages into the same chat orchestration core."""

from __future__ import annotations

from typing import Any

from aethos_core.config import get_settings


def extract_telegram_text(update: dict[str, Any]) -> tuple[str, str, str] | None:
    message = update.get("message") or update.get("edited_message")
    if not isinstance(message, dict):
        return None
    chat = message.get("chat") if isinstance(message.get("chat"), dict) else {}
    from_user = message.get("from") if isinstance(message.get("from"), dict) else {}
    text = str(message.get("text") or "").strip()
    chat_id = str(chat.get("id") or "")
    user_id = str(from_user.get("id") or "")
    if not text or not chat_id:
        return None
    return text, chat_id, user_id


def handle_telegram_update(update: dict[str, Any]) -> dict[str, Any]:
    """Process one Telegram update through unified channel inbound routing."""
    from aethos_core.channels.telegram.telegram_runtime import telegram_configured

    if not telegram_configured():
        return {"ok": False, "reason": "telegram_not_configured"}

    from aethos_core.channels.channel_registry import get_channel_adapter
    from aethos_core.channels.inbound import handle_channel_message
    from aethos_core.channels.telegram.telegram_token import resolve_telegram_bot_token

    settings = get_settings()
    bot_token, _ = resolve_telegram_bot_token()
    if not bot_token:
        return {"ok": False, "reason": "telegram_not_configured"}

    adapter = get_channel_adapter("telegram")
    if adapter is None:
        return {"ok": False, "reason": "telegram_adapter_missing"}

    msg = adapter.normalize_payload(update)
    if not msg:
        return {"ok": True, "skipped": True}

    from aethos_core.channels.activity import telegram_activity_session

    # §4 — live progress mirror: narrate tool-loop steps into one editable
    # "working…" message while the turn runs. Read-only visibility; the final
    # reply below is unchanged. No-op for quick turns and when disabled.
    mirror = None
    sink_token = None
    if settings.telegram_progress_message_enabled:
        from aethos_core.channels.telegram.chat_action import TelegramProgressMirror
        from aethos_core.execution_brain.agent_tool_executor import (
            live_progress_enabled,
            set_progress_sink,
        )

        if live_progress_enabled():
            mirror = TelegramProgressMirror(token=bot_token, chat_id=msg.external_chat_id)
            sink_token = set_progress_sink(mirror.on_event)

    try:
        with telegram_activity_session(
            chat_id=msg.external_chat_id,
            session_id=msg.session_id,
            user_text=msg.text,
            token=bot_token,
        ):
            turn = handle_channel_message(msg)
    finally:
        if sink_token is not None:
            from aethos_core.execution_brain.agent_tool_executor import reset_progress_sink

            reset_progress_sink(sink_token)
        if mirror is not None:
            mirror.finish()
    if not turn.ok:
        return {
            "ok": False,
            "session_id": turn.session_id,
            "reason": "chat_resolution_failed",
            "detail": turn.error or "unknown",
        }

    sent = adapter.send_message(chat_id=msg.external_chat_id, text=turn.reply)
    from aethos_core.channels.telegram.telegram_activity import record_outbound

    record_outbound(
        chat_id=msg.external_chat_id,
        session_id=msg.session_id,
        ok=sent,
        error="" if sent else "send_failed",
    )
    return {
        "ok": sent,
        "session_id": turn.session_id,
        "intent": turn.intent,
        "used_llm": turn.used_llm,
    }
