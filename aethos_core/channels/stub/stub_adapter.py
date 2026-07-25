# SPDX-License-Identifier: Apache-2.0
"""Stub channel adapters — structured not-configured responses for planned transports."""

from __future__ import annotations

from typing import Any

from aethos_core.channels.base.channel_adapter import ChannelAdapter, ChannelMessage


class StubChannelAdapter(ChannelAdapter):
    """Placeholder transport — never executes orchestration; returns not-configured guidance."""

    def __init__(self, *, name: str, label: str) -> None:
        self.name = name
        self.label = label

    def normalize_payload(self, payload: dict[str, Any]) -> ChannelMessage | None:
        _ = payload
        return None

    def send_message(self, *, chat_id: str, text: str) -> bool:
        _ = chat_id, text
        return False

    def not_configured_reply(self) -> str:
        return (
            f"**{self.label}** is not configured yet in this AethOS instance.\n\n"
            "Use **Web / Mission Control** or **Telegram** for governed orchestration today."
        )

    def is_configured(self) -> bool:
        return False
