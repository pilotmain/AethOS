# SPDX-License-Identifier: Apache-2.0
"""Universal channel runtime — governed adapters across all surfaces."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Any

from aethos_core.channels.base.channel_adapter import ChannelAdapter, ChannelMessage


def _settings_str(attr: str) -> str:
    from aethos_core.config import get_settings

    return str(getattr(get_settings(), attr, "") or "").strip()


class GovernedChannelAdapter(ChannelAdapter):
    """Base for universal channels — transport only, same orchestration brain."""

    governed: bool = True

    def handle_inbound(self, payload: dict[str, Any]) -> dict[str, Any]:
        from aethos_core.channels.inbound import handle_channel_message

        msg = self.normalize_payload(payload)
        if msg is None:
            return {"ok": False, "error": "Could not normalize payload"}
        result = handle_channel_message(msg)
        outbound: dict[str, Any] = {
            "ok": result.ok,
            "reply": result.reply,
            "session_id": result.session_id,
            "channel": result.channel,
            "intent": result.intent,
            "meta": result.meta,
            "governance": "same_brain_same_audit",
        }
        if result.ok and msg.external_chat_id:
            self.send_message(chat_id=msg.external_chat_id, text=result.reply)
        return outbound


def _send_smtp_email(*, to_addr: str, subject: str, body: str) -> bool:
    from aethos_core.config import get_settings

    settings = get_settings()
    if settings.sendgrid_api_key.strip():
        return _send_sendgrid_email(to_addr=to_addr, subject=subject, body=body)
    host = str(settings.smtp_host or "").strip()
    if not host:
        return False
    msg = EmailMessage()
    msg["From"] = str(settings.email_from or settings.smtp_user or "aethos@localhost")
    msg["To"] = to_addr
    msg["Subject"] = subject[:200] or "AethOS reply"
    msg.set_content(body)
    try:
        with smtplib.SMTP(host, int(settings.smtp_port or 587), timeout=20) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            user = str(settings.smtp_user or "").strip()
            password = str(settings.smtp_password or "").strip()
            if user and password:
                smtp.login(user, password)
            smtp.send_message(msg)
        return True
    except (OSError, smtplib.SMTPException):
        return False


def _send_sendgrid_email(*, to_addr: str, subject: str, body: str) -> bool:
    import httpx

    from aethos_core.config import get_settings

    settings = get_settings()
    api_key = str(settings.sendgrid_api_key or "").strip()
    from_addr = str(settings.email_from or "aethos@localhost").strip()
    if not api_key:
        return False
    payload = {
        "personalizations": [{"to": [{"email": to_addr}]}],
        "from": {"email": from_addr},
        "subject": subject[:200] or "AethOS reply",
        "content": [{"type": "text/plain", "value": body[:50000]}],
    }
    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
            )
        return response.status_code < 400
    except httpx.HTTPError:
        return False


def _send_twilio_sms(*, to_number: str, body: str) -> bool:
    import httpx

    from aethos_core.config import get_settings

    settings = get_settings()
    sid = str(settings.twilio_account_sid or "").strip()
    token = str(settings.twilio_auth_token or "").strip()
    from_number = str(settings.twilio_sms_from or "").strip()
    if not sid or not token or not from_number or not to_number.strip():
        return False
    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                auth=(sid, token),
                data={"From": from_number, "To": to_number, "Body": body[:1500]},
            )
        return response.status_code < 400
    except httpx.HTTPError:
        return False


def _send_teams_webhook(*, text: str) -> bool:
    import httpx

    from aethos_core.config import get_settings

    url = str(get_settings().teams_webhook_url or "").strip()
    if not url or not text.strip():
        return False
    payload = {"type": "message", "text": text[:7000]}
    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(url, json=payload)
        return response.status_code < 400
    except httpx.HTTPError:
        return False


def _send_whatsapp_cloud(*, to_number: str, body: str) -> bool:
    import httpx

    from aethos_core.channels.channel_credentials import channel_field

    token = channel_field("whatsapp", "access_token", _settings_str("whatsapp_access_token"))
    phone_id = channel_field("whatsapp", "phone_number_id", _settings_str("whatsapp_phone_number_id"))
    if not token or not phone_id or not to_number.strip() or not body.strip():
        return False
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number.strip(),
        "type": "text",
        "text": {"body": body[:4000]},
    }
    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(
                f"https://graph.facebook.com/v21.0/{phone_id}/messages",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=payload,
            )
        return response.status_code < 400
    except httpx.HTTPError:
        return False


def _send_messenger(*, recipient_id: str, body: str) -> bool:
    import httpx

    from aethos_core.channels.channel_credentials import channel_field

    token = channel_field("messenger", "page_access_token", _settings_str("messenger_page_access_token"))
    if not token or not recipient_id.strip() or not body.strip():
        return False
    payload = {"recipient": {"id": recipient_id.strip()}, "message": {"text": body[:2000]}}
    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(
                "https://graph.facebook.com/v21.0/me/messages",
                params={"access_token": token},
                json=payload,
            )
        return response.status_code < 400
    except httpx.HTTPError:
        return False


def build_twiml_say(text: str) -> str:
    safe = (text or "No response").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<?xml version="1.0" encoding="UTF-8"?><Response><Say>{safe[:1200]}</Say></Response>'


class SlackAdapter(GovernedChannelAdapter):
    name = "slack"
    label = "Slack"

    def normalize_payload(self, payload: dict[str, Any]) -> ChannelMessage | None:
        text = payload.get("text") or payload.get("message")
        if not text:
            return None
        return ChannelMessage(
            channel="slack",
            external_user_id=str(payload.get("user_id", "unknown")),
            external_chat_id=str(payload.get("channel_id", "unknown")),
            text=str(text),
            session_id=f"slack:{payload.get('channel_id', 'default')}",
            raw=payload,
        )

    def send_message(self, *, chat_id: str, text: str) -> bool:
        return False  # Requires credentials — governed stub


class DiscordAdapter(GovernedChannelAdapter):
    name = "discord"
    label = "Discord"

    def normalize_payload(self, payload: dict[str, Any]) -> ChannelMessage | None:
        if payload.get("type") == 1:
            return None
        text = payload.get("content") or payload.get("text")
        if not text and isinstance(payload.get("data"), dict):
            text = payload["data"].get("content")
        if not text:
            return None
        user_id = str(payload.get("author_id") or payload.get("member", {}).get("user", {}).get("id") or "unknown")
        channel_id = str(payload.get("channel_id") or "unknown")
        from aethos_core.channels.discord.discord_identity import discord_session_id

        return ChannelMessage(
            channel="discord",
            external_user_id=user_id,
            external_chat_id=channel_id,
            text=str(text),
            session_id=discord_session_id(channel_id=channel_id, user_id=user_id),
            raw=payload,
        )

    def send_message(self, *, chat_id: str, text: str) -> bool:
        from aethos_core.channels.channel_credentials import channel_field

        token = channel_field("discord", "bot_token", _settings_str("discord_bot_token"))
        if not token or not chat_id.strip() or not text.strip():
            return False
        import httpx

        headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}
        body = {"content": text[:1900]}
        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.post(
                    f"https://discord.com/api/v10/channels/{chat_id}/messages",
                    headers=headers,
                    json=body,
                )
            return response.status_code < 400
        except httpx.HTTPError:
            return False

    def is_configured(self) -> bool:
        from aethos_core.channels.channel_credentials import channel_has_vault_credentials

        if channel_has_vault_credentials("discord"):
            return True
        from aethos_core.config import get_settings

        return bool(get_settings().discord_enabled and str(get_settings().discord_bot_token or "").strip())


class EmailAdapter(GovernedChannelAdapter):
    name = "email"
    label = "Email"

    def normalize_payload(self, payload: dict[str, Any]) -> ChannelMessage | None:
        text = payload.get("body") or payload.get("text") or payload.get("subject")
        if not text:
            return None
        sender = str(payload.get("from") or payload.get("sender") or "unknown")
        thread = str(payload.get("thread_id") or payload.get("message_id") or sender)
        return ChannelMessage(
            channel="email",
            external_user_id=sender,
            external_chat_id=sender,
            text=str(text),
            session_id=f"email:{thread}",
            raw=payload,
        )

    def send_message(self, *, chat_id: str, text: str) -> bool:
        from aethos_core.config import get_settings

        if not get_settings().email_enabled:
            return False
        subject = "AethOS reply"
        return _send_smtp_email(to_addr=chat_id, subject=subject, body=text)

    def is_configured(self) -> bool:
        from aethos_core.config import get_settings

        settings = get_settings()
        if not settings.email_enabled:
            return False
        return bool(settings.sendgrid_api_key.strip() or settings.smtp_host.strip())


class TeamsAdapter(GovernedChannelAdapter):
    name = "teams"
    label = "Microsoft Teams"

    def normalize_payload(self, payload: dict[str, Any]) -> ChannelMessage | None:
        text = payload.get("text") or payload.get("body")
        if not text and isinstance(payload.get("message"), dict):
            text = payload["message"].get("text")
        if not text:
            return None
        user = payload.get("from")
        user_id = str(user.get("id") if isinstance(user, dict) else user or "unknown")
        conversation = payload.get("conversation")
        conversation_id = str(
            conversation.get("id") if isinstance(conversation, dict) else payload.get("conversation_id") or "unknown"
        )
        return ChannelMessage(
            channel="teams",
            external_user_id=user_id,
            external_chat_id=conversation_id,
            text=str(text),
            session_id=f"teams:{conversation_id}",
            raw=payload,
        )

    def send_message(self, *, chat_id: str, text: str) -> bool:
        from aethos_core.config import get_settings

        _ = chat_id
        if not get_settings().teams_enabled:
            return False
        return _send_teams_webhook(text=text)

    def is_configured(self) -> bool:
        from aethos_core.config import get_settings

        settings = get_settings()
        return bool(settings.teams_enabled and str(settings.teams_webhook_url or "").strip())


class SmsAdapter(GovernedChannelAdapter):
    name = "sms"
    label = "SMS"

    def normalize_payload(self, payload: dict[str, Any]) -> ChannelMessage | None:
        text = payload.get("Body") or payload.get("body") or payload.get("text")
        if not text:
            return None
        sender = str(payload.get("From") or payload.get("from") or "unknown")
        return ChannelMessage(
            channel="sms",
            external_user_id=sender,
            external_chat_id=sender,
            text=str(text),
            session_id=f"sms:{sender}",
            raw=payload,
        )

    def send_message(self, *, chat_id: str, text: str) -> bool:
        from aethos_core.config import get_settings

        if not get_settings().sms_enabled:
            return False
        return _send_twilio_sms(to_number=chat_id, body=text)

    def is_configured(self) -> bool:
        from aethos_core.config import get_settings

        settings = get_settings()
        return bool(
            settings.sms_enabled
            and settings.twilio_account_sid.strip()
            and settings.twilio_auth_token.strip()
            and settings.twilio_sms_from.strip()
        )


class VoiceAdapter(GovernedChannelAdapter):
    name = "voice"
    label = "Voice"

    def normalize_payload(self, payload: dict[str, Any]) -> ChannelMessage | None:
        text = payload.get("SpeechResult") or payload.get("Body") or payload.get("text")
        if not text:
            return None
        caller = str(payload.get("From") or payload.get("from") or "unknown")
        return ChannelMessage(
            channel="voice",
            external_user_id=caller,
            external_chat_id=caller,
            text=str(text),
            session_id=f"voice:{caller}",
            raw=payload,
        )

    def send_message(self, *, chat_id: str, text: str) -> bool:
        _ = chat_id
        return bool(text.strip())

    def handle_inbound(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = super().handle_inbound(payload)
        if result.get("ok") and result.get("reply"):
            result["twiml"] = build_twiml_say(str(result["reply"]))
        return result

    def is_configured(self) -> bool:
        from aethos_core.config import get_settings

        settings = get_settings()
        return bool(
            settings.voice_enabled
            and settings.twilio_account_sid.strip()
            and settings.twilio_auth_token.strip()
        )


class WhatsAppAdapter(GovernedChannelAdapter):
    name = "whatsapp"
    label = "WhatsApp"

    def normalize_payload(self, payload: dict[str, Any]) -> ChannelMessage | None:
        # Meta WhatsApp Cloud webhook: entry[].changes[].value.messages[]
        try:
            entries = payload.get("entry") or []
            for entry in entries:
                for change in entry.get("changes") or []:
                    value = change.get("value") or {}
                    for message in value.get("messages") or []:
                        text = (message.get("text") or {}).get("body") or message.get("button", {}).get("text")
                        if not text:
                            continue
                        sender = str(message.get("from") or "unknown")
                        return ChannelMessage(
                            channel="whatsapp",
                            external_user_id=sender,
                            external_chat_id=sender,
                            text=str(text),
                            session_id=f"whatsapp:{sender}",
                            raw=message,
                        )
        except (AttributeError, TypeError):
            return None
        # Flat shape (test/manual): {"from": ..., "text": ...}
        text = payload.get("text") or payload.get("body")
        if not text:
            return None
        sender = str(payload.get("from") or "unknown")
        return ChannelMessage(
            channel="whatsapp",
            external_user_id=sender,
            external_chat_id=sender,
            text=str(text),
            session_id=f"whatsapp:{sender}",
            raw=payload,
        )

    def send_message(self, *, chat_id: str, text: str) -> bool:
        if not self.is_configured():
            return False
        return _send_whatsapp_cloud(to_number=chat_id, body=text)

    def is_configured(self) -> bool:
        from aethos_core.channels.channel_credentials import channel_has_vault_credentials

        if channel_has_vault_credentials("whatsapp"):
            return True
        from aethos_core.config import get_settings

        settings = get_settings()
        return bool(
            settings.whatsapp_enabled
            and str(settings.whatsapp_access_token or "").strip()
            and str(settings.whatsapp_phone_number_id or "").strip()
        )


class MessengerAdapter(GovernedChannelAdapter):
    name = "messenger"
    label = "Messenger"

    def normalize_payload(self, payload: dict[str, Any]) -> ChannelMessage | None:
        # Meta Messenger webhook: entry[].messaging[]
        try:
            for entry in payload.get("entry") or []:
                for event in entry.get("messaging") or []:
                    message = event.get("message") or {}
                    text = message.get("text")
                    if not text:
                        continue
                    sender = str((event.get("sender") or {}).get("id") or "unknown")
                    return ChannelMessage(
                        channel="messenger",
                        external_user_id=sender,
                        external_chat_id=sender,
                        text=str(text),
                        session_id=f"messenger:{sender}",
                        raw=event,
                    )
        except (AttributeError, TypeError):
            return None
        text = payload.get("text") or payload.get("body")
        if not text:
            return None
        sender = str(payload.get("from") or "unknown")
        return ChannelMessage(
            channel="messenger",
            external_user_id=sender,
            external_chat_id=sender,
            text=str(text),
            session_id=f"messenger:{sender}",
            raw=payload,
        )

    def send_message(self, *, chat_id: str, text: str) -> bool:
        if not self.is_configured():
            return False
        return _send_messenger(recipient_id=chat_id, body=text)

    def is_configured(self) -> bool:
        from aethos_core.channels.channel_credentials import channel_has_vault_credentials

        if channel_has_vault_credentials("messenger"):
            return True
        from aethos_core.config import get_settings

        settings = get_settings()
        return bool(settings.messenger_enabled and str(settings.messenger_page_access_token or "").strip())


_ADAPTERS: dict[str, GovernedChannelAdapter] = {
    "slack": SlackAdapter(),
    "discord": DiscordAdapter(),
    "email": EmailAdapter(),
    "teams": TeamsAdapter(),
    "sms": SmsAdapter(),
    "voice": VoiceAdapter(),
    "whatsapp": WhatsAppAdapter(),
    "messenger": MessengerAdapter(),
}


def list_universal_channels() -> dict[str, Any]:
    from aethos_core.channels.channel_registry import channel_registry_payload

    channels: list[dict[str, Any]] = [
        {"name": "telegram", "status": "active", "governed": True},
        {"name": "web", "status": "active", "governed": True},
    ]
    for row in channel_registry_payload().get("channels") or []:
        name = str(row.get("name") or "")
        if name in ("web", "telegram"):
            continue
        channels.append({
            "name": name,
            "label": row.get("label") or name.title(),
            "status": row.get("status") or "stub",
            "configured": bool(row.get("configured")),
            "transport_ready": bool(row.get("transport_ready")),
            "governed": True,
            "same_orchestration": True,
        })
    return {
        "ok": True,
        "invariant": "same orchestration brain, governance, memory, audit across all channels",
        "channels": channels,
        "autonomous_execution_blocked": True,
    }


def route_channel_inbound(*, channel: str, payload: dict[str, Any]) -> dict[str, Any]:
    adapter = _ADAPTERS.get(channel)
    if adapter is None:
        from aethos_core.channels.channel_registry import get_channel_adapter

        registered = get_channel_adapter(channel)
        if registered is None:
            return {"ok": False, "error": f"Unknown channel: {channel}"}
        msg = registered.normalize_payload(payload)
        if msg is None:
            return {"ok": False, "error": "Could not normalize payload"}
        from aethos_core.channels.inbound import handle_channel_message

        turn = handle_channel_message(msg)
        if turn.ok:
            registered.send_message(chat_id=msg.external_chat_id, text=turn.reply)
        return {
            "ok": turn.ok,
            "reply": turn.reply,
            "session_id": turn.session_id,
            "channel": turn.channel,
            "intent": turn.intent,
            "meta": turn.meta,
        }
    return adapter.handle_inbound(payload)
