# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_telegram_webhook_accepts_empty_payload_when_configured():
    from aethos_core.api.main import app

    with patch("aethos_core.channels.telegram.telegram_runtime.telegram_configured", return_value=True):
        with patch(
            "aethos_core.channels.telegram.telegram_router.handle_telegram_update",
            return_value={"ok": True, "skipped": True},
        ):
            with TestClient(app) as client:
                r = client.post("/api/v1/channels/telegram/webhook", json={})
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_telegram_webhook_returns_503_when_not_configured():
    from aethos_core.api.main import app

    with patch("aethos_core.channels.telegram.telegram_runtime.telegram_configured", return_value=False):
        with TestClient(app) as client:
            r = client.post("/api/v1/channels/telegram/webhook", json={})
    assert r.status_code == 503


def test_telegram_webhook_survives_handler_exception():
    from aethos_core.api.main import app

    with patch("aethos_core.channels.telegram.telegram_runtime.telegram_configured", return_value=True):
        with patch(
            "aethos_core.channels.telegram.telegram_router.handle_telegram_update",
            side_effect=RuntimeError("boom"),
        ):
            with TestClient(app) as client:
                r = client.post("/api/v1/channels/telegram/webhook", json={"message": {"text": "hi"}})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False
    assert body["code"] == "TELEGRAM_WEBHOOK_HANDLER_FAILED"


def test_telegram_router_survives_chat_resolution_failure():
    from aethos_core.channels.telegram.telegram_router import handle_telegram_update

    update = {
        "message": {
            "chat": {"id": 12345},
            "from": {"id": 99},
            "text": "hi",
        }
    }
    with patch("aethos_core.channels.telegram.telegram_runtime.telegram_configured", return_value=True):
        with patch(
            "aethos_core.channels.telegram.telegram_token.resolve_telegram_bot_token",
            return_value=("test-token", None),
        ):
            with patch("aethos_core.config.get_settings") as mock_settings:
                mock_settings.return_value.telegram_progress_message_enabled = False
                mock_settings.return_value.channel_gateway_enabled = False
                with patch("aethos_core.chat.service.resolve_chat_turn", side_effect=RuntimeError("chat boom")):
                    with patch(
                        "aethos_core.channels.telegram.telegram_adapter.TelegramChannelAdapter.send_message",
                        return_value=False,
                    ):
                        out = handle_telegram_update(update)
    assert out["ok"] is False
