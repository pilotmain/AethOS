# SPDX-License-Identifier: Apache-2.0
"""Channel adapter contract — transport only, no orchestration."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChannelMessage:
    channel: str
    external_user_id: str
    external_chat_id: str
    text: str
    session_id: str
    raw: dict[str, Any] = field(default_factory=dict)


class ChannelAdapter(ABC):
    name: str
    label: str

    @abstractmethod
    def normalize_payload(self, payload: dict[str, Any]) -> ChannelMessage | None: ...

    @abstractmethod
    def send_message(self, *, chat_id: str, text: str) -> bool: ...

    def send_job_update(self, *, chat_id: str, message: str) -> bool:
        return self.send_message(chat_id=chat_id, text=message)
