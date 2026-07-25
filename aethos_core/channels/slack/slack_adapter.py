# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from aethos_core.channels.base.channel_adapter import ChannelAdapter, ChannelMessage
from aethos_core.channels.slack.slack_router import extract_slack_event
from aethos_core.channels.slack.slack_runtime import slack_bot_token, slack_configured
from aethos_core.channels.slack.slack_transport import send_slack_message


class SlackChannelAdapter(ChannelAdapter):
    name = "slack"
    label = "Slack"

    def normalize_payload(self, payload: dict[str, Any]) -> ChannelMessage | None:
        parsed = extract_slack_event(payload)
        if not parsed:
            return None
        text, channel_id, user_id, session_id = parsed
        return ChannelMessage(
            channel=self.name,
            external_user_id=user_id,
            external_chat_id=channel_id,
            text=text,
            session_id=session_id,
            raw=payload,
        )

    def send_message(self, *, chat_id: str, text: str) -> bool:
        token = slack_bot_token()
        if not token:
            return False
        return send_slack_message(token=token, channel_id=chat_id, text=text)

    def is_configured(self) -> bool:
        return slack_configured()
