# SPDX-License-Identifier: Apache-2.0
"""Channel health questions route to live status — not workspace/GitHub lanes."""

from unittest.mock import patch

from aethos_core.channels.channel_registry import compose_channel_health_reply, is_channel_health_request


def test_is_channel_health_request_telegram():
    assert is_channel_health_request("what's wrong with telegram?")
    assert is_channel_health_request("investigate why telegram is failing")
    assert not is_channel_health_request("register local repo /tmp/foo")


def test_compose_telegram_health_includes_webhook_and_error():
    status = {
        "token_configured": True,
        "token_source": "vault",
        "transport_health": "ok",
        "channel_gateway_enabled": True,
        "expected_webhook_url": "https://pilotmain.com/aethos-api/api/v1/channels/telegram/webhook",
        "webhook_mismatch": True,
        "webhook": {"url": "https://stale.ngrok-free.dev/webhook"},
        "last_received_at": None,
        "last_sent_at": 1_700_000_000,
        "last_send_ok": False,
        "last_send_error": "Bad Request: chat not found",
    }
    with patch(
        "aethos_core.channels.telegram.telegram_runtime.telegram_channel_status",
        return_value=status,
    ):
        out = compose_channel_health_reply("what's wrong with telegram?")
    assert out is not None
    body, intent, meta = out
    assert intent == "telegram_channel_health"
    assert "stale.ngrok-free.dev" in body
    assert "chat not found" in body
    assert "Register production webhook" in body
    assert "NGROK_AUTHTOKEN" not in body
    assert meta.get("lane") == "channel_health"
