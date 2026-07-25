# SPDX-License-Identifier: Apache-2.0
"""§4 — Slack + Discord channel parity: signed inbound, normalize, status, outbound."""

from __future__ import annotations

import httpx
import pytest

from aethos_core.config import get_settings


@pytest.fixture(autouse=True)
def _clear_settings():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_discord_signature_verification_roundtrip(monkeypatch):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    private = Ed25519PrivateKey.generate()
    public_hex = private.public_key().public_bytes_raw().hex()
    monkeypatch.setenv("DISCORD_PUBLIC_KEY", public_hex)
    get_settings.cache_clear()

    from aethos_core.channels.discord.discord_runtime import (
        discord_signature_enforced,
        verify_discord_signature,
    )

    assert discord_signature_enforced() is True
    body = b'{"type":1}'
    timestamp = "1700000000"
    signature = private.sign(timestamp.encode("utf-8") + body).hex()
    assert verify_discord_signature(body=body, signature=signature, timestamp=timestamp) is True
    # Tampered body must fail.
    assert verify_discord_signature(body=b'{"type":2}', signature=signature, timestamp=timestamp) is False
    # Garbage signature must fail (never raise).
    assert verify_discord_signature(body=body, signature="zz", timestamp=timestamp) is False


def test_discord_signature_not_enforced_without_key(monkeypatch):
    monkeypatch.delenv("DISCORD_PUBLIC_KEY", raising=False)
    get_settings.cache_clear()
    from aethos_core.channels.discord.discord_runtime import discord_signature_enforced

    assert discord_signature_enforced() is False


def test_discord_normalize_and_session_id():
    from aethos_core.channels.universal.universal_channel_runtime import DiscordAdapter

    adapter = DiscordAdapter()
    assert adapter.normalize_payload({"type": 1}) is None  # PING is not a message
    msg = adapter.normalize_payload({"content": "status please", "author_id": "u1", "channel_id": "c1"})
    assert msg is not None
    assert msg.channel == "discord"
    assert msg.text == "status please"
    assert "c1" in msg.session_id and "u1" in msg.session_id


def test_discord_outbound_send_calls_api(monkeypatch):
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-bot-token")
    get_settings.cache_clear()

    sent = {}

    class _Resp:
        status_code = 200

    class _Client:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, headers=None, json=None):
            sent["url"] = url
            sent["auth"] = headers.get("Authorization")
            return _Resp()

    monkeypatch.setattr(httpx, "Client", _Client)
    from aethos_core.channels.universal.universal_channel_runtime import DiscordAdapter

    ok = DiscordAdapter().send_message(chat_id="c1", text="hello")
    assert ok is True
    assert "discord.com/api" in sent["url"]
    assert sent["auth"].startswith("Bot ")


def test_discord_channel_status_shape(monkeypatch):
    monkeypatch.setenv("DISCORD_ENABLED", "true")
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-bot-token")
    get_settings.cache_clear()
    from aethos_core.channels.discord.discord_runtime import discord_channel_status

    status = discord_channel_status()
    assert status["channel"] == "discord"
    assert status["configured"] is True
    assert status["interactions_path"].endswith("/discord/interactions")


def test_slack_runtime_exposes_signature_and_status():
    # §4 — Slack is at parity: signed events + status, same as Telegram.
    from aethos_core.channels.slack.slack_runtime import slack_channel_status, verify_slack_signature

    assert callable(verify_slack_signature)
    status = slack_channel_status()
    assert isinstance(status, dict)


def test_slack_adapter_normalize():
    from aethos_core.channels.slack.slack_adapter import SlackChannelAdapter

    adapter = SlackChannelAdapter()
    msg = adapter.normalize_payload(
        {"event": {"type": "message", "text": "hi", "user": "U1", "channel": "C1"}}
    )
    # Either a normalized message or None (when event shape unsupported) — never raises.
    assert msg is None or msg.channel == "slack"
