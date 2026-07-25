# SPDX-License-Identifier: Apache-2.0
"""Normalize Slack Events API payloads."""

from __future__ import annotations

from typing import Any

from aethos_core.channels.slack.slack_runtime import slack_session_id


def extract_slack_event(payload: dict[str, Any]) -> tuple[str, str, str, str] | None:
    if payload.get("type") == "url_verification":
        return None
    event = payload.get("event")
    if not isinstance(event, dict):
        return None
    if event.get("bot_id") or event.get("subtype"):
        return None
    text = str(event.get("text") or "").strip()
    channel_id = str(event.get("channel") or "")
    user_id = str(event.get("user") or "")
    if not text or not channel_id:
        return None
    session_id = slack_session_id(channel_id=channel_id, user_id=user_id or channel_id)
    return text, channel_id, user_id, session_id


def handle_slack_event(payload: dict[str, Any]) -> dict[str, Any]:
    from aethos_core.channels.channel_registry import get_channel_adapter
    from aethos_core.channels.inbound import handle_channel_message
    from aethos_core.channels.slack.slack_runtime import slack_configured
    from aethos_core.config import get_settings

    if payload.get("type") == "url_verification":
        return {"ok": True, "challenge": payload.get("challenge")}

    settings = get_settings()
    if not settings.slack_enabled or not slack_configured():
        return {"ok": False, "reason": "slack_not_configured"}

    adapter = get_channel_adapter("slack")
    if adapter is None:
        return {"ok": False, "reason": "slack_adapter_missing"}

    msg = adapter.normalize_payload(payload)
    if not msg:
        return {"ok": True, "skipped": True}

    turn = handle_channel_message(msg)
    if not turn.ok:
        return {"ok": False, "session_id": turn.session_id, "detail": turn.error or "chat_failed"}

    sent = adapter.send_message(chat_id=msg.external_chat_id, text=turn.reply)
    return {
        "ok": sent,
        "session_id": turn.session_id,
        "intent": turn.intent,
        "used_llm": turn.used_llm,
    }
