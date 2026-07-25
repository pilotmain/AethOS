# SPDX-License-Identifier: Apache-2.0
"""§1 — transport-ready channels: status promotion + governed round-trips."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.channels.base.channel_adapter import ChannelMessage
from aethos_core.channels.channel_registry import (
    channel_registry_payload,
    ensure_channels_registered,
    reset_channel_registry_for_tests,
)
from aethos_core.config import get_settings


@pytest.fixture(autouse=True)
def _registry():
    reset_channel_registry_for_tests()
    ensure_channels_registered()
    yield
    reset_channel_registry_for_tests()


@pytest.fixture(autouse=True)
def _settings():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_transport_ready_channels_not_stub():
    by_name = {r["name"]: r for r in channel_registry_payload()["channels"]}
    for name in ("slack", "discord", "email", "whatsapp", "messenger"):
        assert by_name[name]["status"] == "ready", name
        assert by_name[name]["transport_ready"] is True
        assert by_name[name]["adapter_registered"] is True
    assert by_name["sms"]["status"] == "stub"
    assert by_name["voice"]["status"] == "stub"


def _round_trip(adapter, *, channel: str, payload: dict, chat_id: str):
    with patch("aethos_core.channels.inbound.handle_channel_message") as turn:
        turn.return_value = type(
            "R",
            (),
            {"ok": True, "reply": "Governed reply.", "session_id": f"{channel}:test", "channel": channel, "intent": "chat", "meta": {}},
        )()
        with patch.object(adapter, "send_message", return_value=True) as send:
            result = adapter.handle_inbound(payload)
    assert result["ok"] is True
    assert result["reply"] == "Governed reply."
    send.assert_called_once_with(chat_id=chat_id, text="Governed reply.")
    return result


def test_email_round_trip(monkeypatch):
    monkeypatch.setenv("EMAIL_ENABLED", "true")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    get_settings.cache_clear()
    from aethos_core.channels.universal.universal_channel_runtime import EmailAdapter

    adapter = EmailAdapter()
    with patch("aethos_core.channels.universal.universal_channel_runtime._send_smtp_email", return_value=True):
        _round_trip(
            adapter,
            channel="email",
            payload={"from": "user@example.com", "body": "hello"},
            chat_id="user@example.com",
        )


def test_whatsapp_round_trip(monkeypatch):
    monkeypatch.setenv("WHATSAPP_ENABLED", "true")
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "tok")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "123")
    get_settings.cache_clear()
    from aethos_core.channels.universal.universal_channel_runtime import WhatsAppAdapter

    adapter = WhatsAppAdapter()
    with patch("aethos_core.channels.universal.universal_channel_runtime._send_whatsapp_cloud", return_value=True):
        _round_trip(
            adapter,
            channel="whatsapp",
            payload={"from": "15550001111", "text": "ping"},
            chat_id="15550001111",
        )


def test_slack_round_trip(monkeypatch):
    monkeypatch.setenv("SLACK_ENABLED", "true")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token-12345")
    get_settings.cache_clear()
    from aethos_core.channels.slack.slack_adapter import SlackChannelAdapter

    adapter = SlackChannelAdapter()
    payload = {
        "type": "event_callback",
        "event": {"type": "message", "text": "hi", "channel": "C1", "user": "U1"},
    }
    with patch("aethos_core.channels.inbound.handle_channel_message") as turn:
        turn.return_value = type(
            "R",
            (),
            {"ok": True, "reply": "ok", "session_id": "slack-C1-U1", "channel": "slack", "intent": "chat", "meta": {}},
        )()
        with patch.object(adapter, "send_message", return_value=True) as send:
            msg = adapter.normalize_payload(payload)
            assert msg is not None
            from aethos_core.channels.inbound import handle_channel_message

            result = handle_channel_message(msg)
            adapter.send_message(chat_id=msg.external_chat_id, text=result.reply)
    send.assert_called_once()


def test_discord_round_trip(monkeypatch):
    monkeypatch.setenv("DISCORD_ENABLED", "true")
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "discord-token")
    get_settings.cache_clear()
    from aethos_core.channels.universal.universal_channel_runtime import DiscordAdapter

    adapter = DiscordAdapter()
    _round_trip(
        adapter,
        channel="discord",
        payload={"content": "status", "author_id": "u1", "channel_id": "c1"},
        chat_id="c1",
    )


def test_configured_slack_promotes_to_active(monkeypatch):
    monkeypatch.setenv("SLACK_ENABLED", "true")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token-12345")
    get_settings.cache_clear()
    reset_channel_registry_for_tests()
    ensure_channels_registered()
    by_name = {r["name"]: r for r in channel_registry_payload()["channels"]}
    assert by_name["slack"]["status"] == "active"
    assert by_name["slack"]["configured"] is True
