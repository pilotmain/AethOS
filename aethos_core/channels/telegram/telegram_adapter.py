# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from aethos_core.channels.base.channel_adapter import ChannelAdapter, ChannelMessage
from aethos_core.channels.telegram.telegram_identity import telegram_session_id
from aethos_core.channels.telegram.telegram_router import extract_telegram_text
from aethos_core.channels.telegram.telegram_transport import send_telegram_message


class TelegramChannelAdapter(ChannelAdapter):
    name = "telegram"
    label = "Telegram"

    def normalize_payload(self, payload: dict[str, Any]) -> ChannelMessage | None:
        parsed = extract_telegram_text(payload)
        if not parsed:
            return None
        text, chat_id, user_id = parsed
        return ChannelMessage(
            channel=self.name,
            external_user_id=user_id,
            external_chat_id=chat_id,
            text=text,
            session_id=telegram_session_id(chat_id=chat_id, user_id=user_id),
            raw=payload,
        )

    def send_message(self, *, chat_id: str, text: str) -> bool:
        from aethos_core.channels.telegram.telegram_token import resolve_telegram_bot_token

        token, _ = resolve_telegram_bot_token()
        if not token:
            return False
        out = send_telegram_message(token=token, chat_id=chat_id, text=text)
        if isinstance(out, dict):
            ok = bool(out.get("ok"))
            detail = str(out.get("detail") or "")
        else:
            ok = bool(out)
            detail = "" if ok else "send_failed"
        from aethos_core.channels.telegram.telegram_activity import record_outbound

        record_outbound(chat_id=chat_id, ok=ok, error="" if ok else detail)
        return ok

    def is_configured(self) -> bool:
        from aethos_core.channels.telegram.telegram_runtime import telegram_configured

        return telegram_configured()
