# SPDX-License-Identifier: Apache-2.0
"""Managed tunnel runtime — Telegram webhook bootstrap."""

from __future__ import annotations

import logging
from time import time
from typing import Any

from aethos_core.config import get_settings
from aethos_core.runtime.tunnel import ngrok_adapter
from aethos_core.runtime.tunnel.tunnel_health import check_tunnel_health
from aethos_core.runtime.tunnel.tunnel_state import get_state, load_persisted_state, reset_runtime_state, update_state

_log = logging.getLogger(__name__)


def bootstrap_tunnel_on_startup() -> dict[str, Any]:
    """Start tunnel when explicitly enabled — never silent."""
    load_persisted_state()
    settings = get_settings()
    if not settings.telegram_tunnel_enabled:
        update_state(provider=settings.tunnel_provider, status="stopped", enabled=False)
        return get_state()
    if settings.tunnel_provider != "ngrok":
        update_state(status="failed", enabled=True, last_error=f"Unsupported TUNNEL_PROVIDER: {settings.tunnel_provider}")
        return get_state()
    return start_tunnel()


def start_tunnel() -> dict[str, Any]:
    settings = get_settings()
    if not settings.telegram_tunnel_enabled:
        return {"ok": False, "error": "tunnel_disabled"}
    result = ngrok_adapter.start_ngrok(port=settings.ngrok_target_port or settings.api_port)
    if not result.get("ok"):
        update_state(
            provider="ngrok",
            status="failed",
            enabled=True,
            local_port=settings.ngrok_target_port or settings.api_port,
            last_error=str(result.get("detail") or result.get("error")),
        )
        return {"ok": False, "state": get_state(), **result}

    public_url = str(result["public_url"])
    webhook_path = "/api/v1/channels/telegram/webhook"
    webhook_url = public_url.rstrip("/") + webhook_path
    wh = _configure_telegram_webhook(webhook_url)
    update_state(
        provider="ngrok",
        status="running",
        enabled=True,
        local_port=result.get("local_port"),
        public_url=public_url,
        webhook_url=webhook_url,
        telegram_webhook_status="configured" if wh.get("ok") else "failed",
        last_started_at=time(),
        last_error=None if wh.get("ok") else wh.get("detail"),
    )
    _log.info("tunnel_started public_url=%s webhook=%s", public_url, webhook_url)
    return {"ok": True, "state": get_state(), "webhook": wh}


def stop_tunnel() -> dict[str, Any]:
    ngrok_adapter.stop_ngrok()
    reset_runtime_state()
    update_state(provider="ngrok", status="stopped", enabled=get_settings().telegram_tunnel_enabled)
    return {"ok": True, "state": get_state()}


def restart_tunnel() -> dict[str, Any]:
    stop_tunnel()
    return start_tunnel()


def tunnel_status() -> dict[str, Any]:
    load_persisted_state()
    state = get_state()
    if state.get("status") == "running" and not ngrok_adapter.is_running():
        update_state(status="failed", last_error="ngrok process exited unexpectedly")
        state = get_state()
    health = check_tunnel_health() if state.get("status") == "running" else {"ok": False, "reachable": False}
    from aethos_core.channels.telegram.telegram_runtime import telegram_channel_status

    telegram = telegram_channel_status(include_webhook=True, flush_delivery=False)
    return {
        "ok": True,
        "tunnel": state,
        "health": health,
        "telegram": {
            "enabled": telegram.get("enabled"),
            "configured": telegram.get("configured"),
            "webhook": telegram.get("webhook"),
        },
    }


def shutdown_tunnel() -> None:
    ngrok_adapter.stop_ngrok()
    reset_runtime_state()


def _configure_telegram_webhook(webhook_url: str) -> dict[str, Any]:
    from aethos_core.channels.telegram.telegram_token import resolve_telegram_bot_token
    from aethos_core.channels.telegram.telegram_transport import set_webhook

    token, _ = resolve_telegram_bot_token()
    if not token:
        return {"ok": False, "detail": "Telegram bot token not configured"}
    return set_webhook(token=token, url=webhook_url)
