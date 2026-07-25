# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import patch

from aethos_core.channels.dispatch import (
    _condense_progress_message,
    clear_progress_state_for_tests,
    dispatch_job_lifecycle,
)
from aethos_core.channels.telegram.telegram_activity import clear_for_tests, record_inbound, record_outbound
from aethos_core.channels.telegram.telegram_runtime import telegram_channel_status


def test_telegram_status_never_leaks_token():
    clear_for_tests()
    with patch("aethos_core.channels.telegram.telegram_runtime.resolve_telegram_bot_token", return_value=("secret-token-12345", "cred-abc")):
        with patch("aethos_core.config.get_settings") as mock_settings:
            mock_settings.return_value.telegram_enabled = True
            mock_settings.return_value.telegram_bot_token = ""
            with patch("aethos_core.channels.telegram.telegram_transport.get_webhook_info", return_value={"ok": True, "url": "https://x/webhook"}):
                status = telegram_channel_status()
    assert status["token_configured"] is True
    assert status["token_source"] == "vault"
    dumped = str(status)
    assert "secret-token" not in dumped


def test_telegram_activity_snapshot():
    clear_for_tests()
    record_inbound(chat_id="111", user_id="9", session_id="tg-111-9", preview="hi")
    record_outbound(chat_id="111", session_id="tg-111-9", ok=True)
    record_inbound(chat_id="222", user_id="1", session_id="tg-222-1", preview="domains")
    status = telegram_channel_status(include_webhook=False)
    assert status["last_received_at"] is not None
    assert status["last_sent_at"] is not None
    assert status["active_chats_count"] == 2
    assert status["active_sessions"]


def test_progress_condensation_suppresses_internal_steps():
    job = SimpleNamespace(params={"target_name": "invoicepilot"})
    assert _condense_progress_message(job, "Resolving auth") is None
    assert _condense_progress_message(job, "Building adapter") is None
    assert _condense_progress_message(job, "Running read-only operation preflight…") == "⏳ Running read-only preflight…"
    condensed = _condense_progress_message(job, "Checking list domains for `invoicepilot` using your saved Vercel API token…")
    assert condensed is not None
    assert "invoicepilot" in condensed


def test_dispatch_sends_approval_hint_on_preflight_complete():
    clear_progress_state_for_tests()
    job = SimpleNamespace(
        id="job-1",
        session_id="tg-12345-99",
        job_type="operation_preflight",
        params={
            "preflight_status": "ready_for_approval",
            "operation_type": "list_domains",
            "target_name": "invoicepilot",
            "operation_preflight": {
                "preflight_status": "ready_for_approval",
                "operation_type": "list_domains",
                "target_name": "invoicepilot",
            },
        },
    )
    with patch("aethos_core.channels.telegram.telegram_runtime.telegram_configured", return_value=True):
        with patch("aethos_core.channels.telegram.telegram_adapter.TelegramChannelAdapter.send_job_update") as send:
            dispatch_job_lifecycle(job, event_type="job_completed", message="Preflight complete.")
    send.assert_called_once()
    body = send.call_args.kwargs["message"]
    assert "Approval required" in body
    assert "invoicepilot" in body


def test_dispatch_skips_verbose_progress():
    clear_progress_state_for_tests()
    job = SimpleNamespace(id="job-2", session_id="tg-99-1", job_type="vercel_domains_execution", params={})
    with patch("aethos_core.channels.telegram.telegram_runtime.telegram_configured", return_value=True):
        with patch("aethos_core.channels.telegram.telegram_adapter.TelegramChannelAdapter.send_job_update") as send:
            dispatch_job_lifecycle(job, event_type="job_progress", message="Building adapter")
    send.assert_not_called()
