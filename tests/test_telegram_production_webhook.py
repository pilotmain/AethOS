# SPDX-License-Identifier: Apache-2.0
"""Telegram production webhook registration and vault-based runtime enablement."""

from unittest.mock import patch

from aethos_core.channels.telegram.telegram_runtime import telegram_configured, telegram_channel_status
from aethos_core.production.deployment_mode import (
    resolve_public_api_base_url,
    telegram_canonical_webhook_url,
)


def test_telegram_configured_with_vault_token_without_env_flag():
    with patch("aethos_core.channels.telegram.telegram_runtime.get_settings") as mock_settings:
        mock_settings.return_value.telegram_enabled = False
        mock_settings.return_value.telegram_bot_token = ""
        mock_settings.return_value.channel_gateway_enabled = True
        with patch(
            "aethos_core.channels.channel_credentials.channel_has_vault_credentials",
            return_value=True,
        ):
            with patch(
                "aethos_core.channels.telegram.telegram_runtime.resolve_telegram_bot_token",
                return_value=("token-abc", "cred-1"),
            ):
                assert telegram_configured() is True


def test_telegram_status_reports_runtime_enabled_from_vault():
    with patch("aethos_core.channels.telegram.telegram_runtime.get_settings") as mock_settings:
        mock_settings.return_value.telegram_enabled = False
        mock_settings.return_value.telegram_bot_token = ""
        mock_settings.return_value.channel_gateway_enabled = True
        with patch(
            "aethos_core.channels.channel_credentials.channel_has_vault_credentials",
            return_value=True,
        ):
            with patch(
                "aethos_core.channels.telegram.telegram_runtime.resolve_telegram_bot_token",
                return_value=("token-abc", "cred-1"),
            ):
                with patch(
                    "aethos_core.channels.telegram.telegram_transport.get_webhook_info",
                    return_value={"ok": True, "url": "https://pilotmain.com/aethos-api/api/v1/channels/telegram/webhook"},
                ):
                    with patch(
                        "aethos_core.production.deployment_mode.is_hosted_deployment",
                        return_value=True,
                    ):
                        with patch(
                            "aethos_core.production.deployment_mode.telegram_canonical_webhook_url",
                            return_value="https://pilotmain.com/aethos-api/api/v1/channels/telegram/webhook",
                        ):
                            status = telegram_channel_status(include_webhook=True)
    assert status["enabled"] is True
    assert status["configured"] is True
    assert status["transport_health"] == "ok"
    assert status["webhook_mismatch"] is False


def test_telegram_status_webhook_mismatch_when_stale_ngrok():
    with patch("aethos_core.channels.telegram.telegram_runtime.get_settings") as mock_settings:
        mock_settings.return_value.telegram_enabled = True
        mock_settings.return_value.telegram_bot_token = "env-token"
        mock_settings.return_value.channel_gateway_enabled = True
        with patch(
            "aethos_core.channels.telegram.telegram_runtime.resolve_telegram_bot_token",
            return_value=("env-token", None),
        ):
            with patch(
                "aethos_core.channels.telegram.telegram_transport.get_webhook_info",
                return_value={
                    "ok": True,
                    "url": "https://stale.ngrok-free.dev/api/v1/channels/telegram/webhook",
                },
            ):
                with patch(
                    "aethos_core.production.deployment_mode.is_hosted_deployment",
                    return_value=True,
                ):
                    with patch(
                        "aethos_core.production.deployment_mode.telegram_canonical_webhook_url",
                        return_value="https://pilotmain.com/aethos-api/api/v1/channels/telegram/webhook",
                    ):
                        status = telegram_channel_status(include_webhook=True)
    assert status["webhook_mismatch"] is True


def test_resolve_public_api_base_url_hosted_default():
    with patch("aethos_core.config.get_settings") as mock_settings:
        mock_settings.return_value.public_app_base_url = ""
        mock_settings.return_value.oidc_redirect_url = ""
        with patch("aethos_core.production.deployment_mode.is_hosted_deployment", return_value=True):
            assert resolve_public_api_base_url() == "https://pilotmain.com/aethos-api"


def test_telegram_canonical_webhook_url_from_public_app_base():
    with patch("aethos_core.config.get_settings") as mock_settings:
        mock_settings.return_value.public_app_base_url = "https://pilotmain.com/aethos"
        mock_settings.return_value.oidc_redirect_url = ""
        with patch("aethos_core.production.deployment_mode.is_hosted_deployment", return_value=False):
            url = telegram_canonical_webhook_url()
    assert url == "https://pilotmain.com/aethos-api/api/v1/channels/telegram/webhook"


def test_register_production_webhook_api():
    from fastapi.testclient import TestClient

    from aethos_core.api.main import app

    canonical = "https://pilotmain.com/aethos-api/api/v1/channels/telegram/webhook"
    with patch(
        "aethos_core.production.deployment_mode.telegram_canonical_webhook_url",
        return_value=canonical,
    ):
        with patch(
            "aethos_core.channels.telegram.telegram_token.resolve_telegram_bot_token",
            return_value=("bot-token", "cred-1"),
        ):
            with patch(
                "aethos_core.channels.telegram.telegram_transport.set_webhook",
                return_value={"ok": True, "detail": "Webhook configured"},
            ) as set_wh:
                with patch(
                    "aethos_core.channels.telegram.telegram_transport.get_webhook_info",
                    return_value={"ok": True, "url": canonical},
                ):
                    with TestClient(app) as client:
                        r = client.post("/api/v1/channels/telegram/webhook/register/production")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["webhook_url"] == canonical
    assert body.get("verified") is True
    set_wh.assert_any_call(token="bot-token", url=canonical)


def test_register_production_webhook_falls_back_to_channel_owner():
    """Regression: when the request does not carry the owner's tenant (so the
    request-scoped token resolves empty), registration must fall back to the
    channel's unique owner — the same resolution the inbound webhook uses —
    instead of returning 'token missing'. Registering is a deployment action and
    must not depend on whose session clicked the button."""
    import contextlib

    from fastapi.testclient import TestClient

    from aethos_core.api.main import app

    canonical = "https://pilotmain.com/aethos-api/api/v1/channels/telegram/webhook"

    @contextlib.contextmanager
    def _owner_scope(_provider):
        yield "rayameha@gmail.com"

    with patch(
        "aethos_core.production.deployment_mode.telegram_canonical_webhook_url",
        return_value=canonical,
    ):
        # 1st call (request scope) → empty; 2nd call (channel-owner scope) → token.
        with patch(
            "aethos_core.channels.telegram.telegram_token.resolve_telegram_bot_token",
            side_effect=[("", None), ("bot-token", "cred-1")],
        ):
            with patch(
                "aethos_core.channels.webhook_tenant.channel_webhook_tenant_scope",
                side_effect=_owner_scope,
            ):
                with patch(
                    "aethos_core.channels.telegram.telegram_transport.set_webhook",
                    return_value={"ok": True, "detail": "Webhook configured"},
                ) as set_wh:
                    with patch(
                        "aethos_core.channels.telegram.telegram_transport.get_webhook_info",
                        return_value={"ok": True, "url": canonical},
                    ):
                        with TestClient(app) as client:
                            r = client.post("/api/v1/channels/telegram/webhook/register/production")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    set_wh.assert_any_call(token="bot-token", url=canonical)


def test_telegram_test_send_propagates_bot_api_detail():
    from fastapi.testclient import TestClient

    from aethos_core.api.main import app

    with patch("aethos_core.channels.telegram.telegram_runtime.telegram_configured", return_value=True):
        with patch(
            "aethos_core.channels.telegram.telegram_token.resolve_telegram_bot_token",
            return_value=("bot-token", "cred-1"),
        ):
            with patch(
                "aethos_core.channels.telegram.telegram_transport.send_telegram_message",
                return_value={"ok": False, "detail": "Bad Request: chat not found"},
            ):
                with TestClient(app) as client:
                    r = client.post(
                        "/api/v1/channels/telegram/test-send",
                        json={"chat_id": "999", "message": "hi"},
                    )
    assert r.status_code == 502
    body = r.json()
    assert body.get("detail") == "Bad Request: chat not found"
    assert "test_send_failed" not in str(body.get("detail") or "")


def test_local_webhook_register_rejected_on_hosted():
    from fastapi.testclient import TestClient

    from aethos_core.api.main import app

    with patch("aethos_core.production.deployment_mode.is_hosted_deployment", return_value=True):
        with TestClient(app) as client:
            r = client.post("/api/v1/channels/telegram/webhook/register")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False
    assert body["error"] == "local_webhook_on_hosted"
