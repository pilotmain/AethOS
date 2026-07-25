# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from aethos_core.channels.telegram.telegram_identity import is_telegram_session, telegram_session_id
from aethos_core.channels.telegram.telegram_router import handle_telegram_update
from aethos_core.chat.service import ChatTurnResult


def test_telegram_session_mapping():
    sid = telegram_session_id(chat_id="12345", user_id="99")
    assert sid.startswith("tg-")
    assert is_telegram_session(sid)


def test_telegram_routes_through_chat_core():
    update = {
        "message": {
            "chat": {"id": 12345},
            "from": {"id": 99},
            "text": "show domains for invoicepilot",
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
                with patch("aethos_core.chat.service.resolve_chat_turn") as mock_turn:
                    mock_turn.return_value = ChatTurnResult(
                        reply="Preflight queued.",
                        intent="operation_preflight",
                    )
                    with patch(
                        "aethos_core.channels.telegram.telegram_adapter.send_telegram_message",
                        return_value=True,
                    ):
                        out = handle_telegram_update(update)
    assert out["ok"] is True
    assert out["session_id"].startswith("tg-")
    mock_turn.assert_called_once()
    assert mock_turn.call_args.kwargs["session_id"] == out["session_id"]
