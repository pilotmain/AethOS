# SPDX-License-Identifier: Apache-2.0
"""WhatsApp/Meta inbound webhooks must verify X-Hub-Signature-256 when an app
secret is configured — closing the open-webhook hole (anyone POSTing forged
inbound messages). Mirrors the Slack/Discord signature enforcement."""

from __future__ import annotations

import hashlib
import hmac
import json
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from aethos_core.api.routes import channels as channels_routes
from aethos_core.channels.meta_webhook import verify_meta_signature
from aethos_core.config import get_settings


def _client() -> TestClient:
    """Minimal app with just the channels router — deterministic (the real app
    mounts channel routes via a background startup task)."""
    app = FastAPI()
    app.include_router(channels_routes.router, prefix="/api/v1")
    return TestClient(app)

APP_SECRET = "test-app-secret"
INBOUND = {
    "object": "whatsapp_business_account",
    "entry": [
        {
            "changes": [
                {
                    "value": {"messages": [{"from": "15550001111", "type": "text", "text": {"body": "hi"}}]},
                    "field": "messages",
                }
            ]
        }
    ],
}


def _sign(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_verify_meta_signature_unit():
    body = b'{"a":1}'
    good = _sign(body, APP_SECRET)
    assert verify_meta_signature(body=body, signature=good, app_secret=APP_SECRET) is True
    assert verify_meta_signature(body=body, signature=good, app_secret="wrong") is False
    assert verify_meta_signature(body=body, signature="sha256=deadbeef", app_secret=APP_SECRET) is False
    assert verify_meta_signature(body=body, signature="", app_secret=APP_SECRET) is False
    assert verify_meta_signature(body=body, signature=good, app_secret="") is False


@pytest.fixture
def wa_enabled(monkeypatch):
    monkeypatch.setenv("WHATSAPP_ENABLED", "true")
    monkeypatch.setenv("WHATSAPP_APP_SECRET", APP_SECRET)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_whatsapp_webhook_rejects_bad_signature(wa_enabled):

    client = _client()
    body = json.dumps(INBOUND).encode()
    r = client.post(
        "/api/v1/channels/whatsapp/webhook",
        content=body,
        headers={"X-Hub-Signature-256": "sha256=bad", "Content-Type": "application/json"},
    )
    assert r.status_code == 401


def test_whatsapp_webhook_accepts_valid_signature(wa_enabled):

    body = json.dumps(INBOUND).encode()
    sig = _sign(body, APP_SECRET)
    with patch(
        "aethos_core.channels.universal.universal_channel_runtime.route_channel_inbound",
        return_value={"ok": True, "skipped": False},
    ) as routed:
        client = _client()
        r = client.post(
            "/api/v1/channels/whatsapp/webhook",
            content=body,
            headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"},
        )
    assert r.status_code == 200
    assert routed.called


def test_whatsapp_webhook_skips_verification_when_no_app_secret(monkeypatch):

    monkeypatch.setenv("WHATSAPP_ENABLED", "true")
    monkeypatch.delenv("WHATSAPP_APP_SECRET", raising=False)
    get_settings.cache_clear()
    try:
        with patch(
            "aethos_core.channels.universal.universal_channel_runtime.route_channel_inbound",
            return_value={"ok": True, "skipped": False},
        ):
            client = _client()
            r = client.post("/api/v1/channels/whatsapp/webhook", json=INBOUND)
        assert r.status_code == 200  # back-compat: no secret yet → setup not blocked
    finally:
        get_settings.cache_clear()


def test_whatsapp_get_verify_handshake(monkeypatch):

    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "myverify")
    get_settings.cache_clear()
    try:
        client = _client()
        ok = client.get(
            "/api/v1/channels/whatsapp/webhook",
            params={"hub.mode": "subscribe", "hub.verify_token": "myverify", "hub.challenge": "C123"},
        )
        assert ok.status_code == 200 and ok.text == "C123"
        bad = client.get(
            "/api/v1/channels/whatsapp/webhook",
            params={"hub.mode": "subscribe", "hub.verify_token": "wrong", "hub.challenge": "C123"},
        )
        assert bad.status_code == 403
    finally:
        get_settings.cache_clear()
