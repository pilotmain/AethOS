# SPDX-License-Identifier: Apache-2.0
"""PWA + web push — subscriptions, delivery, automation hook (PATH §4)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.automation.delivery import deliver_automation_message
from aethos_core.config import get_settings
from aethos_core.pwa.push_store import clear_push_subscriptions_for_tests, list_push_subscriptions, save_push_subscription
from aethos_core.pwa.web_push import notify_tenant_web_push, pwa_status, web_push_enabled
from aethos_core.tenancy.tenant_context import tenant_scope


@pytest.fixture(autouse=True)
def _reset_push(monkeypatch):
    clear_push_subscriptions_for_tests()
    monkeypatch.setenv("WEB_PUSH_ENABLED", "false")
    monkeypatch.delenv("VAPID_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("VAPID_PRIVATE_KEY", raising=False)
    yield
    clear_push_subscriptions_for_tests()


def test_pwa_status_default_off():
    status = pwa_status()
    assert status["pwa_installable"] is True
    assert status["web_push_enabled"] is False


def test_push_subscription_store_round_trip(monkeypatch):
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "true")
    sub = {
        "endpoint": "https://push.example.com/sub/abc",
        "keys": {"p256dh": "key1", "auth": "auth1"},
    }
    with tenant_scope("tenant-pwa"):
        result = save_push_subscription(sub)
        assert result["ok"] is True
        rows = list_push_subscriptions()
    assert len(rows) == 1
    assert rows[0]["endpoint"] == sub["endpoint"]


def test_notify_skips_when_disabled():
    out = notify_tenant_web_push(title="Hi", body="Test")
    assert out.get("skipped") is True


def test_notify_sends_when_configured(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "web_push_enabled", True)
    monkeypatch.setattr(s, "vapid_public_key", "test-public")
    monkeypatch.setattr(s, "vapid_private_key", "test-private")
    assert web_push_enabled() is True

    with tenant_scope("default"):
        save_push_subscription(
            {"endpoint": "https://push.example.com/sub/1", "keys": {"p256dh": "k", "auth": "a"}}
        )

    with patch("pywebpush.webpush", return_value=None) as push:
        out = notify_tenant_web_push(title="Automation", body="Done", tenant_id="default")
    assert out.get("sent", 0) >= 1
    assert push.call_count >= 1


def test_automation_delivery_includes_web_push(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "web_push_enabled", True)
    monkeypatch.setattr(s, "vapid_public_key", "pub")
    monkeypatch.setattr(s, "vapid_private_key", "priv")
    with tenant_scope("default"):
        save_push_subscription(
            {"endpoint": "https://push.example.com/sub/2", "keys": {"p256dh": "k", "auth": "a"}}
        )
    with patch("pywebpush.webpush", return_value=None):
        result = deliver_automation_message(
            session_id="web-default",
            channel="web",
            message="Scheduled summary",
            title="Morning check",
        )
    assert result["ok"] is True
    assert result["web_push"] is not None
    assert result["web_push"].get("sent", 0) >= 1


def test_pwa_status_api():
    client = TestClient(app)
    res = client.get("/api/v1/pwa/status")
    assert res.status_code == 200
    body = res.json()
    assert body["offline_shell"] is True
