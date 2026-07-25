# SPDX-License-Identifier: Apache-2.0
"""Telegram channel runtime status."""

from __future__ import annotations

from typing import Any

from aethos_core.channels.channel_credentials import channel_runtime_enabled
from aethos_core.channels.telegram.telegram_auth import TelegramAuthAdapter
from aethos_core.channels.telegram.telegram_token import resolve_telegram_bot_token
from aethos_core.config import get_settings
from aethos_core.security.credential_vault import get_credential_vault_diagnostics


def telegram_runtime_enabled() -> bool:
    s = get_settings()
    return channel_runtime_enabled("telegram", s.telegram_enabled)


def telegram_configured() -> bool:
    if not telegram_runtime_enabled():
        return False
    token, _ = resolve_telegram_bot_token()
    return bool(token)


def telegram_channel_status(
    *,
    include_webhook: bool = True,
    flush_delivery: bool = False,
    request=None,
) -> dict[str, Any]:
    from aethos_core.channels.telegram.chat_action import typing_diagnostics
    from aethos_core.channels.telegram.telegram_activity import activity_snapshot
    from aethos_core.channels.telegram.telegram_delivery import flush_queue, queue_snapshot
    from aethos_core.channels.telegram.telegram_preferences import preferences_snapshot
    from aethos_core.channels.telegram.telegram_sessions import list_telegram_sessions
    from aethos_core.channels.telegram.telegram_transport import _bot_api, get_webhook_info
    from aethos_core.production.deployment_mode import is_hosted_deployment, telegram_canonical_webhook_url

    s = get_settings()
    token, cred_id = resolve_telegram_bot_token()
    if token and flush_delivery:
        flush_queue(bot_api_fn=_bot_api, limit=5)

    runtime_enabled = telegram_runtime_enabled()
    token_present = bool(token)
    vault_token = cred_id is not None
    env_token = token_present and not vault_token and bool(s.telegram_bot_token.strip())
    configured = bool(runtime_enabled and token_present)
    activity = activity_snapshot()
    conn = TelegramAuthAdapter().connection_status().to_dict()

    gateway_enabled = bool(getattr(s, "channel_gateway_enabled", False))
    if configured:
        if is_hosted_deployment() and not gateway_enabled:
            transport_health = "gateway_disabled"
        else:
            transport_health = "ok"
    elif not runtime_enabled:
        transport_health = "disabled"
    else:
        transport_health = "token_missing"

    expected_webhook_url = telegram_canonical_webhook_url(request)
    webhook: dict[str, Any] = {"configured": False}
    webhook_mismatch = False
    if include_webhook and token_present:
        wh = get_webhook_info(token=token)
        if wh.get("ok"):
            registered_url = str(wh.get("url") or "")
            webhook = {
                "configured": bool(registered_url),
                "url": registered_url,
                "pending_update_count": wh.get("pending_update_count", 0),
                "last_error_message": wh.get("last_error_message"),
            }
            if expected_webhook_url and registered_url:
                webhook_mismatch = registered_url.rstrip("/") != expected_webhook_url.rstrip("/")
        else:
            transport_health = "degraded" if transport_health == "ok" else transport_health
            webhook = {"configured": False, "error": wh.get("detail")}

    delivery_total = int(activity.get("outbound_success_count") or 0) + int(
        activity.get("outbound_fail_count") or 0
    )
    delivery_rate = None
    if delivery_total > 0:
        delivery_rate = round(
            (int(activity.get("outbound_success_count") or 0) / delivery_total) * 100,
            1,
        )

    return {
        "name": "telegram",
        "label": "Telegram",
        "category": "communications",
        "kind": "channel",
        "configured": configured,
        "connection_state": "connected" if configured else "disconnected",
        "enabled": runtime_enabled,
        "channel_gateway_enabled": gateway_enabled,
        "token_configured": token_present,
        "token_source": "vault" if vault_token else ("env" if env_token else "none"),
        "transport_health": transport_health,
        "webhook_path": "/api/v1/channels/telegram/webhook",
        "expected_webhook_url": expected_webhook_url,
        "webhook_mismatch": webhook_mismatch,
        "webhook": webhook,
        "readonly_execution_via_mc": True,
        "approvals_via_mc": True,
        "last_received_at": activity.get("last_received_at"),
        "last_sent_at": activity.get("last_sent_at"),
        "active_chats_count": activity.get("active_chats_count"),
        "last_send_ok": activity.get("last_send_ok"),
        "last_send_error": activity.get("last_send_error"),
        "delivery_success_rate": delivery_rate,
        "delivery_queue": queue_snapshot(),
        "notification_preferences": preferences_snapshot(),
        "credentials": conn.get("credentials") or [],
        "connected_methods": conn.get("connected_methods") or {},
        "credential_vault": get_credential_vault_diagnostics(),
        "active_sessions": list_telegram_sessions(limit=10),
        "typing": typing_diagnostics(),
        "telegram_api_status": transport_health,
    }
