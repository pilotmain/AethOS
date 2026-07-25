# SPDX-License-Identifier: Apache-2.0
"""Phase 9.8E.6.3 — Telegram typing indicator + progress feedback."""

from __future__ import annotations

import asyncio
import threading
import time
from unittest.mock import patch

import pytest

from aethos_core.channels.activity import (
    TelegramActivitySession,
    TelegramChannelActivityAdapter,
    infer_channel_activity_type,
    progress_message_for_activity,
    telegram_activity_session,
)
from aethos_core.channels.telegram.chat_action import clear_typing_diagnostics_for_tests, typing_diagnostics
from aethos_core.channels.telegram.telegram_router import handle_telegram_update
from aethos_core.chat.service import ChatTurnResult


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.channels.telegram.telegram_activity import clear_for_tests

    clear_for_tests()
    clear_typing_diagnostics_for_tests()
    yield
    clear_for_tests()
    clear_typing_diagnostics_for_tests()


@pytest.fixture
def telegram_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_ENABLED", "true")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "1234567890:ABCDEFghijklmnopqrstuvwxyz")
    monkeypatch.setenv("CHANNEL_GATEWAY_ENABLED", "false")
    monkeypatch.setenv("TELEGRAM_TYPING_ENABLED", "true")
    monkeypatch.setenv("TELEGRAM_PROGRESS_MESSAGE_ENABLED", "true")
    monkeypatch.setenv("TELEGRAM_PROGRESS_AFTER_SECONDS", "1")
    monkeypatch.setenv("TELEGRAM_TYPING_INTERVAL_SECONDS", "2")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _update(text: str = "hello") -> dict:
    return {"message": {"chat": {"id": 12345}, "from": {"id": 99}, "text": text}}


def _chat_result(reply: str = "Hi", intent: str = "greeting") -> ChatTurnResult:
    return ChatTurnResult(reply=reply, intent=intent)


def test_infer_activity_types():
    assert infer_channel_activity_type("Search latest Railway deployment rollback guidance") == "research"
    assert infer_channel_activity_type("capture screenshot of useinvoicepilot.com") == "browser_evidence"
    assert infer_channel_activity_type("analyze why the latest Railway deployment failed") == "multi_agent"
    assert infer_channel_activity_type("hello") == "default_chat"


def test_progress_copy_task_aware():
    assert "researching live sources" in progress_message_for_activity("research").lower()


@patch("aethos_core.channels.telegram.telegram_adapter.TelegramChannelAdapter.send_message", return_value=True)
@patch("aethos_core.channels.telegram.chat_action.send_chat_action_sync", return_value=True)
def test_webhook_starts_typing_before_processing(mock_typing, mock_send, telegram_env):
    typing_before_chat = threading.Event()
    chat_lock = threading.Event()

    def _slow_chat(*args, **kwargs):
        chat_lock.set()
        time.sleep(0.15)
        return _chat_result()

    def _typing(**kwargs):
        if not chat_lock.is_set():
            typing_before_chat.set()
        return True

    mock_typing.side_effect = _typing
    with patch("aethos_core.chat.service.resolve_chat_turn", side_effect=_slow_chat):
        out = handle_telegram_update(_update("hello"))
    assert out["ok"] is True
    assert mock_typing.called
    assert typing_before_chat.is_set()


@patch("aethos_core.channels.telegram.telegram_adapter.TelegramChannelAdapter.send_message", return_value=True)
@patch("aethos_core.channels.telegram.chat_action.send_chat_action_sync", return_value=True)
def test_typing_stops_after_response(mock_typing, mock_send, telegram_env):
    session = telegram_activity_session(chat_id="12345", session_id="tg-12345-99", user_text="hello")
    with session:
        time.sleep(0.05)
    calls_before = mock_typing.call_count
    time.sleep(0.2)
    assert mock_typing.call_count == calls_before


@patch("aethos_core.channels.telegram.telegram_delivery.deliver_message")
def test_long_task_sends_one_progress_message(mock_deliver, telegram_env):
    progress_calls: list[str] = []

    def _send(*, token, chat_id, text, bot_api_fn):
        if "researching live sources" in text.lower():
            progress_calls.append(text)
        return True

    mock_deliver.side_effect = _send
    session = TelegramActivitySession(chat_id="12345", session_id="tg-1", activity_type="research")
    session._progress_worker()
    assert len(progress_calls) == 1


@patch("aethos_core.channels.telegram.telegram_adapter.TelegramChannelAdapter.send_message", return_value=True)
@patch(
    "aethos_core.channels.telegram.telegram_transport._bot_api",
    return_value={"ok": False, "detail": "403 bot blocked by user", "status_code": 403},
)
def test_typing_failure_does_not_fail_chat(mock_api, mock_send, telegram_env):
    with patch("aethos_core.chat.service.resolve_chat_turn", return_value=_chat_result("ok")):
        out = handle_telegram_update(_update("hello"))
    assert out["ok"] is True
    assert typing_diagnostics()["last_typing_error"]


def test_typing_disabled_skips_send(telegram_env, monkeypatch):
    monkeypatch.setenv("TELEGRAM_TYPING_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    with patch("aethos_core.channels.telegram.chat_action.send_chat_action_sync") as mock_typing:
        with patch("aethos_core.channels.telegram.telegram_adapter.TelegramChannelAdapter.send_message", return_value=True):
            with patch("aethos_core.chat.service.resolve_chat_turn", return_value=_chat_result("ok")):
                handle_telegram_update(_update("hello"))
    mock_typing.assert_not_called()


@patch("aethos_core.channels.telegram.telegram_transport.send_telegram_message", return_value=True)
def test_progress_not_spammed(mock_send, telegram_env):
    session = TelegramActivitySession(chat_id="12345", session_id="tg-spam", activity_type="research")
    with session:
        time.sleep(1.2)
        session._progress_sent.set()
        time.sleep(1.2)
    progress_msgs = [str(c) for c in mock_send.call_args_list if "researching live sources" in str(c).lower()]
    assert len(progress_msgs) <= 1


@patch("aethos_core.channels.telegram.chat_action.send_chat_action_sync", return_value=True)
def test_typing_uses_passed_token_when_in_thread_resolution_fails(mock_typing, telegram_env):
    """Regression: the typing thread runs as a daemon and does NOT inherit the
    request's tenant contextvar, so re-resolving a vault-stored (tenant-scoped)
    bot token there returns empty and typing silently no-ops. The request thread
    resolves the token under scope and threads it in; the typing thread must use
    that token rather than resolving it again.
    """
    # Simulate the lost-scope condition: in-thread resolution yields nothing.
    with patch(
        "aethos_core.channels.telegram.telegram_token.resolve_telegram_bot_token",
        return_value=("", None),
    ):
        session = telegram_activity_session(
            chat_id="12345",
            session_id="tg-scoped",
            user_text="hello",
            token="1234567890:ABCDEFghijklmnopqrstuvwxyz",
        )
        with session:
            time.sleep(0.05)
    assert mock_typing.called, "typing must fire using the threaded-in token"
    # The passed token (not the empty in-thread resolution) must reach the API.
    sent_token = mock_typing.call_args.kwargs.get("token")
    assert sent_token == "1234567890:ABCDEFghijklmnopqrstuvwxyz"


@patch("aethos_core.channels.telegram.chat_action.send_chat_action_sync", return_value=True)
def test_router_threads_resolved_token_into_typing(mock_typing, telegram_env):
    """End-to-end: the webhook handler resolves the token and the typing thread
    must send even if in-thread resolution is broken."""
    with patch(
        "aethos_core.channels.telegram.telegram_token.resolve_telegram_bot_token",
        side_effect=[
            # 1st call: request thread (router) resolves a real token under scope.
            ("1234567890:ABCDEFghijklmnopqrstuvwxyz", None),
            # any later in-thread call would fail (no tenant scope).
            ("", None),
            ("", None),
        ],
    ):
        with patch(
            "aethos_core.channels.telegram.telegram_adapter.TelegramChannelAdapter.send_message",
            return_value=True,
        ):
            with patch("aethos_core.chat.service.resolve_chat_turn", return_value=_chat_result("ok")):
                out = handle_telegram_update(_update("hello"))
    assert out["ok"] is True
    assert mock_typing.called


@pytest.mark.asyncio
async def test_telegram_channel_activity_adapter(telegram_env):
    adapter = TelegramChannelActivityAdapter()
    with patch("aethos_core.channels.telegram.chat_action.send_typing") as mock_typing:
        mock_typing.return_value = None
        await adapter.start_activity("sess-1", "research", chat_id="123")
        await asyncio.sleep(0.05)
        await adapter.stop_activity("sess-1")
    assert mock_typing.called
