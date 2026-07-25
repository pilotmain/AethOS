# SPDX-License-Identifier: Apache-2.0
"""Unified inbound channel routing — all transports → orchestration brain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aethos_core.channels.base.channel_adapter import ChannelMessage


@dataclass
class ChannelTurnResult:
    ok: bool
    reply: str
    session_id: str
    channel: str
    intent: str | None = None
    used_llm: bool = False
    meta: dict[str, Any] | None = None
    error: str | None = None


_PUBLIC_OPERATOR_CHANNELS = frozenset({"web", "chat", "cli", "mcp", "webchat"})


def _maybe_pairing_gate(msg: ChannelMessage) -> ChannelTurnResult | None:
    """Channel Gateway pairing gate (handoff §6).

    When the gateway is on and DM policy is pairing, an inbound message from an
    unknown sender on an external channel is NOT processed: it gets a pairing code
    and the operator must approve it. Default-off — existing channel behavior is
    unchanged until CHANNEL_GATEWAY_ENABLED is set. The operator's own web/CLI
    surfaces are never gated.
    """
    from aethos_core.config import get_settings

    settings = get_settings()
    if not getattr(settings, "channel_gateway_enabled", False):
        return None
    channel = (msg.channel or "").strip().lower()
    if channel in _PUBLIC_OPERATOR_CHANNELS:
        return None
    if str(getattr(settings, "channel_dm_policy", "pairing")).strip().lower() != "pairing":
        return None

    from aethos_core.channels.pairing_store import is_sender_allowed, request_pairing

    if is_sender_allowed(channel, msg.external_user_id):
        return None

    pairing = request_pairing(channel, msg.external_user_id, preview=msg.text)
    code = str(pairing.get("code") or "")
    reply = (
        "This channel requires pairing before AethOS will process your messages. "
        f"Pairing code: {code}. Ask the operator to approve it in "
        f"Mission Control → Channels → Pending pairings, "
        f"or run `aethos pairing approve {channel} {code}`."
    )
    return ChannelTurnResult(
        ok=True,
        reply=reply,
        session_id=msg.session_id,
        channel=msg.channel,
        intent="channel_pairing_required",
        used_llm=False,
        meta={"pairing": "pending", "pairing_code": code, "processed": "false"},
    )


def handle_channel_message(msg: ChannelMessage) -> ChannelTurnResult:
    """Route normalized inbound message through resolve_chat_turn — no channel-specific brains."""
    from aethos_core.chat.service import resolve_chat_turn

    # Record inbound activity before the pairing gate — a message from a pending
    # (not-yet-approved) sender is still received, so "last received" must update
    # even when the turn is gated and not processed.
    if msg.channel == "telegram":
        from aethos_core.channels.telegram.telegram_activity import record_inbound

        record_inbound(
            chat_id=msg.external_chat_id,
            user_id=msg.external_user_id,
            session_id=msg.session_id,
            preview=msg.text,
        )

    gated = _maybe_pairing_gate(msg)
    if gated is not None:
        return gated

    try:
        result = resolve_chat_turn(msg.text, session_id=msg.session_id, channel=msg.channel)
        from aethos_core.chat.cognition_exception_boundary import sanitize_chat_result_for_transport

        result = sanitize_chat_result_for_transport(result)
    except Exception as exc:
        from aethos_core.chat.cognition_exception_boundary import (
            CognitionBoundaryContext,
            compose_cognition_crash_fallback,
        )

        result = compose_cognition_crash_fallback(
            exc,
            CognitionBoundaryContext(
                text=msg.text,
                session_id=msg.session_id,
                user_id=msg.external_user_id,
                channel=msg.channel,
            ),
        )

    if msg.channel == "telegram" and result.intent:
        from aethos_core.channels.telegram.telegram_activity import record_session_operation

        record_session_operation(session_id=msg.session_id, operation=str(result.intent))

    reply = (result.reply or "").strip() or "(no response)"
    from aethos_core.runtime.operational_environment import stamp_external_channel_reply

    reply = stamp_external_channel_reply(reply, channel=msg.channel)
    return ChannelTurnResult(
        ok=True,
        reply=reply,
        session_id=msg.session_id,
        channel=msg.channel,
        intent=result.intent,
        used_llm=result.used_llm,
        meta=dict(getattr(result, "meta", None) or {}),
    )
