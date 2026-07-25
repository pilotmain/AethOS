# SPDX-License-Identifier: Apache-2.0
"""Channel registry — register transports, resolve adapters (Phase 9.8A)."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.channels.base.channel_adapter import ChannelAdapter
from aethos_core.channels.registry import (
    ChannelSpec,
    _CHANNEL_SPECS,
    _TRANSPORT_READY_CHANNELS,
    format_channel_summary,
    get_channel,
    list_channels,
)

_registered = False


def _enable_transport_capabilities(spec: ChannelSpec) -> None:
    spec.capabilities.inbound = True
    spec.capabilities.outbound = True
    spec.capabilities.approval_transport = True
    spec.capabilities.evidence_transport = True


def _bind_channel_adapter(spec: ChannelSpec, adapter: ChannelAdapter) -> None:
    """Attach adapter and set honest status: ready (transport) or active (configured)."""
    spec.adapter = adapter
    configured = bool(getattr(adapter, "is_configured", lambda: False)())
    if spec.name in _TRANSPORT_READY_CHANNELS:
        spec.status = "active" if configured else "ready"
        _enable_transport_capabilities(spec)
        return
    if configured:
        spec.status = "active"
        _enable_transport_capabilities(spec)


def ensure_channels_registered() -> None:
    global _registered
    if _registered:
        return

    from aethos_core.channels.slack.slack_adapter import SlackChannelAdapter
    from aethos_core.channels.telegram.telegram_adapter import TelegramChannelAdapter
    from aethos_core.channels.universal.universal_channel_runtime import (
        DiscordAdapter,
        EmailAdapter,
        MessengerAdapter,
        SmsAdapter,
        TeamsAdapter,
        VoiceAdapter,
        WhatsAppAdapter,
    )
    from aethos_core.channels.web.web_adapter import WebChannelAdapter

    _CHANNEL_SPECS["web"].adapter = WebChannelAdapter()
    _CHANNEL_SPECS["telegram"].adapter = TelegramChannelAdapter()
    _bind_channel_adapter(_CHANNEL_SPECS["slack"], SlackChannelAdapter())
    _bind_channel_adapter(_CHANNEL_SPECS["discord"], DiscordAdapter())
    for name, adapter in (
        ("email", EmailAdapter()),
        ("teams", TeamsAdapter()),
        ("sms", SmsAdapter()),
        ("voice", VoiceAdapter()),
        ("whatsapp", WhatsAppAdapter()),
        ("messenger", MessengerAdapter()),
    ):
        spec = _CHANNEL_SPECS.get(name)
        if spec and spec.adapter is None:
            _bind_channel_adapter(spec, adapter)

    _registered = True


def reset_channel_registry_for_tests() -> None:
    global _registered
    from aethos_core.channels.registry import _CHANNEL_SPECS as specs

    _registered = False
    defaults = {
        "web": "active",
        "telegram": "active",
        "email": "ready",
        "slack": "ready",
        "discord": "ready",
        "whatsapp": "ready",
        "messenger": "ready",
        "teams": "stub",
        "sms": "stub",
        "voice": "stub",
    }
    for spec in specs.values():
        spec.adapter = None
        if spec.name in defaults:
            spec.status = defaults[spec.name]
        spec.capabilities.inbound = spec.name in ("web", "telegram")
        spec.capabilities.outbound = spec.name in ("web", "telegram")
        spec.capabilities.approval_transport = spec.name in ("web", "telegram")
        spec.capabilities.evidence_transport = spec.name in ("web", "telegram")


def get_channel_adapter(name: str) -> ChannelAdapter | None:
    ensure_channels_registered()
    spec = get_channel(name)
    if not spec:
        return None
    return spec.adapter


def resolve_adapter_for_session(session_id: str) -> ChannelAdapter | None:
    from aethos_core.channels.session_identity import parse_session_channel

    return get_channel_adapter(parse_session_channel(session_id))


def channel_registry_payload(*, include_planned: bool = True) -> dict[str, Any]:
    ensure_channels_registered()
    rows: list[dict[str, Any]] = []
    for spec in list_channels(include_planned=include_planned):
        adapter = spec.adapter
        configured = bool(getattr(adapter, "is_configured", lambda: spec.status == "active")())
        rows.append(
            {
                "name": spec.name,
                "label": spec.label,
                "status": spec.status,
                "transport_ready": spec.status in ("ready", "active"),
                "adapter_registered": adapter is not None,
                "configured": configured,
                "capabilities": {
                    "inbound": spec.capabilities.inbound,
                    "outbound": spec.capabilities.outbound,
                    "approval_transport": spec.capabilities.approval_transport,
                    "evidence_transport": spec.capabilities.evidence_transport,
                },
            }
        )
    return {
        "ok": True,
        "channels": rows,
        "summary": "Channels are transports only — all intelligence routes through the orchestration brain.",
    }


def channel_status_payload(name: str) -> dict[str, Any]:
    ensure_channels_registered()
    spec = get_channel(name)
    if not spec:
        return {"ok": False, "error": "unknown_channel", "channel": name}
    adapter = spec.adapter
    payload: dict[str, Any] = {
        "ok": True,
        "channel": spec.name,
        "label": spec.label,
        "status": spec.status,
        "transport_ready": spec.status in ("ready", "active"),
        "adapter_registered": adapter is not None,
        "configured": bool(getattr(adapter, "is_configured", lambda: spec.status == "active")()),
    }
    if spec.name == "telegram":
        from aethos_core.channels.telegram.telegram_runtime import telegram_channel_status

        payload["runtime"] = telegram_channel_status(include_webhook=False)
    if spec.name == "slack":
        from aethos_core.channels.slack.slack_runtime import slack_channel_status

        payload["runtime"] = slack_channel_status()
    if spec.name == "discord":
        from aethos_core.channels.discord.discord_runtime import discord_channel_status

        payload["runtime"] = discord_channel_status()
    for channel_name, flag_name in (
        ("email", "email_enabled"),
        ("teams", "teams_enabled"),
        ("sms", "sms_enabled"),
        ("voice", "voice_enabled"),
        ("whatsapp", "whatsapp_enabled"),
        ("messenger", "messenger_enabled"),
    ):
        if spec.name == channel_name:
            from aethos_core.config import get_settings

            settings = get_settings()
            adapter = spec.adapter
            payload["runtime"] = {
                "enabled": bool(getattr(settings, flag_name, False)),
                "configured": bool(getattr(adapter, "is_configured", lambda: False)()),
            }
    from aethos_core.runtime.operational_environment import resolve_operational_environment

    payload["operational_environment"] = resolve_operational_environment().to_dict()
    return payload


_CHANNEL_NAME_RX = re.compile(r"\b(telegram|slack|discord|whatsapp)\b", re.I)
_CHANNEL_HEALTH_RX = re.compile(
    r"\b("
    r"what'?s\s+wrong"
    r"|why\s+(?:is|are)"
    r"|not\s+working"
    r"|failing"
    r"|broken"
    r"|investigate"
    r"|diagnos"
    r"|health"
    r"|status"
    r")\b",
    re.I,
)


def _detect_channel_health_name(text: str) -> str | None:
    m = _CHANNEL_NAME_RX.search((text or "").strip())
    return m.group(1).lower() if m else None


def is_channel_health_request(text: str) -> bool:
    """True when the operator asks about a messaging channel's health — not repo/workspace ops."""
    raw = (text or "").strip()
    if not raw or not _CHANNEL_NAME_RX.search(raw):
        return False
    if not _CHANNEL_HEALTH_RX.search(raw):
        return False
    from aethos_core.chat.explicit_mutation_intent import has_explicit_mutation_verb

    if has_explicit_mutation_verb(raw):
        return False
    return True


def _format_ts(ts: float | int | None) -> str:
    if not ts:
        return "Never"
    try:
        from datetime import datetime

        return datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d %H:%M UTC")
    except (OSError, OverflowError, ValueError):
        return str(ts)


def _compose_telegram_health_reply(status: dict[str, Any]) -> str:
    webhook = status.get("webhook") or {}
    registered = str(webhook.get("url") or "—")
    expected = str(status.get("expected_webhook_url") or "—")
    mismatch = bool(status.get("webhook_mismatch"))
    last_recv = _format_ts(status.get("last_received_at"))
    last_sent = _format_ts(status.get("last_sent_at"))
    send_err = str(status.get("last_send_error") or "").strip()
    transport = str(status.get("transport_health") or "unknown")
    token_src = str(status.get("token_source") or "none")
    gateway = bool(status.get("channel_gateway_enabled"))

    lines = [
        "## Telegram channel status",
        "",
        f"- **Token:** {'configured' if status.get('token_configured') else 'missing'} (source: {token_src})",
        f"- **Transport:** {transport}",
        f"- **Channel gateway:** {'enabled' if gateway else 'disabled on API'}",
        "",
        "### Inbound (webhook)",
        f"- **Registered webhook:** `{registered}`",
        f"- **Expected (production):** `{expected}`",
        f"- **Webhook mismatch:** {'yes — Telegram is not delivering here' if mismatch else 'no'}",
        f"- **Last received:** {last_recv}",
        "",
        "### Outbound (send)",
        f"- **Last sent:** {last_sent}",
        f"- **Last send OK:** {status.get('last_send_ok')}",
    ]
    if send_err:
        lines.append(f"- **Last send error:** {send_err}")
    else:
        lines.append("- **Last send error:** —")

    lines.append("")
    if mismatch and expected and expected != "—":
        lines.append(
            f"**Fix:** open **Connections → Telegram** and click **Register production webhook** "
            f"so Telegram delivers to `{expected}`."
        )
    elif not status.get("token_configured"):
        lines.append("**Fix:** add a bot token under **Connections → Telegram**.")
    elif not gateway:
        lines.append("**Fix:** set `CHANNEL_GATEWAY_ENABLED=true` on the API service and redeploy.")
    elif send_err:
        lines.append("**Fix:** resolve the outbound error above (bad chat id, revoked token, etc.).")
    else:
        lines.append("Channel looks configured — if messages still fail, re-register the production webhook and retry test send.")
    return "\n".join(lines)


def compose_channel_health_reply(
    text: str,
    *,
    request=None,
) -> tuple[str, str, dict[str, str]] | None:
    """Answer channel health from live runtime status — never local workspace / guessed env vars."""
    if not is_channel_health_request(text):
        return None
    channel = _detect_channel_health_name(text)
    if not channel:
        return None
    if channel == "telegram":
        from aethos_core.channels.telegram.telegram_runtime import telegram_channel_status

        status = telegram_channel_status(include_webhook=True, request=request)
        body = _compose_telegram_health_reply(status)
        meta = {
            "lane": "channel_health",
            "route_id": "channel_health",
            "channel": "telegram",
            "read_only": "true",
            "webhook_mismatch": "true" if status.get("webhook_mismatch") else "false",
            "last_send_error": str(status.get("last_send_error") or ""),
        }
        return body, "telegram_channel_health", meta
    payload = channel_status_payload(channel)
    if not payload.get("ok"):
        return (
            f"I don't have diagnostics for channel `{channel}` yet.",
            "channel_health_unknown",
            {"lane": "channel_health", "channel": channel},
        )
    runtime = payload.get("runtime") or {}
    body = (
        f"## {payload.get('label', channel)} status\n\n"
        f"- Configured: **{payload.get('configured')}**\n"
        f"- Runtime: {runtime}"
    )
    return body, f"{channel}_channel_health", {
        "lane": "channel_health",
        "route_id": "channel_health",
        "channel": channel,
        "read_only": "true",
    }
