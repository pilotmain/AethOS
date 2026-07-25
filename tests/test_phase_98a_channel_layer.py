# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from aethos_core.channels.channel_registry import (
    channel_registry_payload,
    ensure_channels_registered,
    get_channel_adapter,
    reset_channel_registry_for_tests,
)
from aethos_core.channels.registry import get_channel
from aethos_core.channels.inbound import handle_channel_message
from aethos_core.channels.outbound import dispatch_job_lifecycle
from aethos_core.channels.session_identity import external_chat_id_from_session, parse_session_channel
from aethos_core.channels.base.channel_adapter import ChannelMessage


@pytest.fixture(autouse=True)
def _reset_registry():
    reset_channel_registry_for_tests()
    ensure_channels_registered()
    yield
    reset_channel_registry_for_tests()


def test_parse_session_channel():
    assert parse_session_channel("tg-123-456") == "telegram"
    assert parse_session_channel("slack-C123-U456") == "slack"
    assert parse_session_channel("default") == "web"
    assert parse_session_channel("web-session-1") == "web"


def test_external_chat_id_from_session():
    assert external_chat_id_from_session("tg-12345-99") == "12345"
    assert external_chat_id_from_session("web-default") is None


def test_channel_registry_registers_adapters():
    payload = channel_registry_payload()
    by_name = {row["name"]: row for row in payload["channels"]}
    assert by_name["telegram"]["adapter_registered"] is True
    assert by_name["web"]["adapter_registered"] is True
    assert by_name["slack"]["adapter_registered"] is True
    assert by_name["slack"]["configured"] is False
    assert by_name["slack"]["status"] == "ready"
    assert by_name["slack"]["transport_ready"] is True
    assert by_name["discord"]["status"] == "ready"
    assert by_name["email"]["status"] == "ready"
    assert by_name["whatsapp"]["status"] == "ready"
    assert by_name["teams"]["status"] == "stub"


def test_stub_adapter_not_configured():
    slack = get_channel_adapter("slack")
    assert slack is not None
    assert slack.is_configured() is False
    assert get_channel("slack") is not None
    assert get_channel("slack").status == "ready"


def test_inbound_routes_to_chat_brain():
    msg = ChannelMessage(
        channel="web",
        external_user_id="u1",
        external_chat_id="default",
        text="show supported channels",
        session_id="web-default",
    )
    with (
        patch("aethos_core.chat.service.resolve_chat_turn") as turn,
        patch(
            "aethos_core.chat.cognition_exception_boundary.sanitize_chat_result_for_transport",
            side_effect=lambda r: r,
        ),
    ):
        turn.return_value = type(
            "R",
            (),
            {"reply": "Channels listed.", "intent": "channels_summary", "used_llm": False, "meta": {}},
        )()
        result = handle_channel_message(msg)
    assert result.ok is True
    assert result.reply == "Channels listed."
    turn.assert_called_once_with("show supported channels", session_id="web-default", channel="web")


def test_outbound_resolves_telegram_adapter():
    from types import SimpleNamespace

    job = SimpleNamespace(
        id="job-tg",
        session_id="tg-12345-99",
        job_type="manual_note",
        params={},
    )
    adapter = get_channel_adapter("telegram")
    with patch.object(adapter, "send_job_update", return_value=True) as send:
        with patch("aethos_core.channels.telegram.telegram_runtime.telegram_configured", return_value=True):
            dispatch_job_lifecycle(job, event_type="job_completed", message="Done.")
    send.assert_called_once()


def test_channels_api_list():
    from aethos_core.api.main import app

    client = TestClient(app)
    res = client.get("/api/v1/channels")
    assert res.status_code == 200
    names = {row["name"] for row in res.json()["channels"]}
    assert "telegram" in names
    assert "slack" in names


def test_partial_railway_intent_still_routes():
    from aethos_core.operations.intents import infer_operation_preflight_intent

    out = infer_operation_preflight_intent("restart speakglobal-ai on Railwa")
    assert out is not None
    assert out[2]["provider"] == "railway"
