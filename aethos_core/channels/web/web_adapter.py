# SPDX-License-Identifier: Apache-2.0
"""Web / Mission Control channel adapter — transport symmetry only."""

from __future__ import annotations

from typing import Any

from aethos_core.channels.base.channel_adapter import ChannelAdapter, ChannelMessage
from aethos_core.channels.session_identity import web_session_id


class WebChannelAdapter(ChannelAdapter):
    name = "web"
    label = "Web / Mission Control"

    def normalize_payload(self, payload: dict[str, Any]) -> ChannelMessage | None:
        text = str(payload.get("message") or payload.get("text") or "").strip()
        if not text:
            return None
        session_key = str(payload.get("session_id") or payload.get("session_key") or "default")
        return ChannelMessage(
            channel=self.name,
            external_user_id=str(payload.get("user_id") or "web-user"),
            external_chat_id=session_key,
            text=text,
            session_id=web_session_id(session_key),
            raw=payload,
        )

    def send_message(self, *, chat_id: str, text: str) -> bool:
        """Web replies are rendered by the client — outbound is a no-op at transport layer."""
        _ = chat_id, text
        return True

    def is_configured(self) -> bool:
        return True
