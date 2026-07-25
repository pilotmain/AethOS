# SPDX-License-Identifier: Apache-2.0
"""§3 — WhatsApp Cloud API + Messenger GovernedChannelAdapters (token+webhook)."""

from __future__ import annotations

import httpx
import pytest

from aethos_core.config import get_settings


@pytest.fixture(autouse=True)
def _clear_settings():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_whatsapp_normalize_meta_cloud_payload():
    from aethos_core.channels.universal.universal_channel_runtime import WhatsAppAdapter

    payload = {
        "entry": [
            {
                "changes": [
                    {"value": {"messages": [{"from": "15550001111", "text": {"body": "status please"}}]}}
                ]
            }
        ]
    }
    msg = WhatsAppAdapter().normalize_payload(payload)
    assert msg is not None
    assert msg.channel == "whatsapp"
    assert msg.text == "status please"
    assert msg.external_user_id == "15550001111"
    assert msg.session_id == "whatsapp:15550001111"


def test_whatsapp_normalize_flat_and_empty():
    from aethos_core.channels.universal.universal_channel_runtime import WhatsAppAdapter

    adapter = WhatsAppAdapter()
    flat = adapter.normalize_payload({"from": "x", "text": "hi"})
    assert flat is not None and flat.text == "hi"
    assert adapter.normalize_payload({"entry": [{"changes": [{"value": {}}]}]}) is None


def test_whatsapp_send_calls_graph_api(monkeypatch):
    monkeypatch.setenv("WHATSAPP_ENABLED", "true")
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "tok")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "999")
    get_settings.cache_clear()

    sent: dict = {}

    class _Resp:
        status_code = 200

    class _Client:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, headers=None, json=None, params=None):
            sent["url"] = url
            sent["json"] = json
            sent["auth"] = (headers or {}).get("Authorization")
            return _Resp()

    monkeypatch.setattr(httpx, "Client", _Client)
    from aethos_core.channels.universal.universal_channel_runtime import WhatsAppAdapter

    ok = WhatsAppAdapter().send_message(chat_id="15550001111", text="hello")
    assert ok is True
    assert "graph.facebook.com" in sent["url"] and "/999/messages" in sent["url"]
    assert sent["auth"] == "Bearer tok"
    assert sent["json"]["messaging_product"] == "whatsapp"


def test_whatsapp_send_disabled_returns_false(monkeypatch):
    monkeypatch.delenv("WHATSAPP_ENABLED", raising=False)
    get_settings.cache_clear()
    from aethos_core.channels.universal.universal_channel_runtime import WhatsAppAdapter

    assert WhatsAppAdapter().send_message(chat_id="x", text="y") is False


def test_whatsapp_is_configured(monkeypatch):
    from aethos_core.channels.universal.universal_channel_runtime import WhatsAppAdapter

    get_settings.cache_clear()
    assert WhatsAppAdapter().is_configured() is False
    monkeypatch.setenv("WHATSAPP_ENABLED", "true")
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "tok")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "999")
    get_settings.cache_clear()
    assert WhatsAppAdapter().is_configured() is True


def test_messenger_normalize_meta_payload():
    from aethos_core.channels.universal.universal_channel_runtime import MessengerAdapter

    payload = {"entry": [{"messaging": [{"sender": {"id": "u9"}, "message": {"text": "hi there"}}]}]}
    msg = MessengerAdapter().normalize_payload(payload)
    assert msg is not None
    assert msg.channel == "messenger"
    assert msg.text == "hi there"
    assert msg.external_user_id == "u9"


def test_new_channels_registered_in_registry():
    from aethos_core.channels.channel_registry import (
        get_channel_adapter,
        reset_channel_registry_for_tests,
    )

    reset_channel_registry_for_tests()
    assert get_channel_adapter("whatsapp") is not None
    assert get_channel_adapter("messenger") is not None
    reset_channel_registry_for_tests()


def test_new_channels_surface_in_catalog():
    from aethos_core.catalog.connection_catalog import _build_channel_catalog

    connected, available = _build_channel_catalog({"name": "telegram", "label": "Telegram", "configured": False})
    names = {e["name"] for e in connected + available}
    assert "whatsapp" in names
    assert "messenger" in names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
