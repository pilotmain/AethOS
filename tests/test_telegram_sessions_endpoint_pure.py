# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_telegram_sessions_endpoint_is_pure_read():
    from aethos_core.api.main import app

    with TestClient(app) as client:
        with patch("aethos_core.channels.telegram.telegram_transport._bot_api") as bot_api:
            with patch("aethos_core.channels.telegram.telegram_delivery.flush_queue") as flush_queue:
                r = client.get("/api/v1/channels/telegram/sessions")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "sessions" in body
    bot_api.assert_not_called()
    flush_queue.assert_not_called()


def test_telegram_status_does_not_flush_delivery_by_default(monkeypatch):
    from aethos_core.api.main import app

    monkeypatch.setenv("TELEGRAM_ENABLED", "true")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "1234567890:ABCDEFghijklmnopqrstuvwxyz")
    monkeypatch.setenv("CHANNEL_GATEWAY_ENABLED", "true")
    from aethos_core.config import get_settings

    get_settings.cache_clear()

    with TestClient(app) as client:
        with patch(
            "aethos_core.channels.telegram.telegram_transport.get_webhook_info",
            return_value={"ok": True, "url": ""},
        ):
            with patch("aethos_core.channels.telegram.telegram_delivery.flush_queue") as flush_queue:
                r = client.get("/api/v1/channels/telegram/status")
    assert r.status_code == 200
    body = r.json()
    assert body.get("token_configured") is True
    assert "secret-token" not in str(body)
    flush_queue.assert_not_called()
    get_settings.cache_clear()


def test_telegram_delivery_flush_endpoint_only():
    from aethos_core.api.main import app

    with TestClient(app) as client:
        with patch("aethos_core.channels.telegram.telegram_runtime.telegram_configured", return_value=True):
            with patch("aethos_core.channels.telegram.telegram_token.resolve_telegram_bot_token", return_value=("1234567890:ABCDEFghijklmnopqrstuvwxyz", None)):
                with patch("aethos_core.channels.telegram.telegram_delivery.flush_queue", return_value={"sent": 1, "failed": 0, "queued": 0}) as flush_queue:
                    r = client.post("/api/v1/channels/telegram/delivery/flush")
    assert r.status_code == 200
    flush_queue.assert_called_once()
