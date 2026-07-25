# SPDX-License-Identifier: Apache-2.0
"""Slack channel — inbound events and outbound chat.postMessage."""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any

from aethos_core.config import get_settings


def slack_session_id(*, channel_id: str, user_id: str) -> str:
    return f"slack:{channel_id}:{user_id}"


def slack_bot_token() -> str:
    from aethos_core.channels.channel_credentials import channel_field

    return channel_field("slack", "bot_token", str(get_settings().slack_bot_token or ""))


def slack_signing_secret() -> str:
    from aethos_core.channels.channel_credentials import channel_field

    return channel_field("slack", "signing_secret", str(get_settings().slack_signing_secret or ""))


def slack_configured() -> bool:
    from aethos_core.channels.channel_credentials import channel_has_vault_credentials

    if channel_has_vault_credentials("slack"):
        return True
    settings = get_settings()
    return bool(settings.slack_enabled and str(settings.slack_bot_token or "").strip())


def slack_channel_status() -> dict[str, Any]:
    settings = get_settings()
    return {
        "ok": True,
        "configured": slack_configured(),
        "enabled": bool(settings.slack_enabled),
        "token_present": bool(slack_bot_token()),
        "signing_secret_present": bool(slack_signing_secret()),
    }


def verify_slack_signature(*, body: bytes, timestamp: str, signature: str) -> bool:
    secret = slack_signing_secret()
    if not secret or not signature or not timestamp:
        return False
    try:
        if abs(time.time() - int(timestamp)) > 60 * 5:
            return False
    except ValueError:
        return False
    base = f"v0:{timestamp}:{body.decode('utf-8')}"
    digest = hmac.new(secret.encode("utf-8"), base.encode("utf-8"), hashlib.sha256).hexdigest()
    expected = f"v0={digest}"
    return hmac.compare_digest(expected, signature)
