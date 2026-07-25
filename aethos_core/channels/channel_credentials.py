# SPDX-License-Identifier: Apache-2.0
"""Generic per-channel credential runtime — vault-backed, multi-field, redacted.

Lets the operator connect any registered channel (Slack, Discord, WhatsApp,
Messenger, …) from the UI exactly like Telegram: secrets stored in the encrypted
credential vault, never echoed. Multi-field credentials (e.g. Slack bot token +
signing secret) are packed as a JSON blob into a single vault credential; the
resolver also reads Telegram's existing plain-token credentials unchanged.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from aethos_core.security.credential_vault import get_credential_vault
from aethos_core.security.secret_redaction import mask_secret


@dataclass(frozen=True)
class ChannelCredentialField:
    id: str
    label: str
    secret: bool = True
    required: bool = True
    placeholder: str = ""
    help: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "secret": self.secret,
            "required": self.required,
            "placeholder": self.placeholder,
            "help": self.help,
        }


@dataclass(frozen=True)
class ChannelCredentialSpec:
    channel_id: str
    label: str
    primary_field: str
    fields: tuple[ChannelCredentialField, ...]
    webhook_path: str | None = None
    default_label: str = ""
    description: str = ""

    def field_ids(self) -> list[str]:
        return [f.id for f in self.fields]

    def required_ids(self) -> list[str]:
        return [f.id for f in self.fields if f.required]

    def to_schema(self) -> dict[str, Any]:
        return {
            "channel_id": self.channel_id,
            "label": self.label,
            "primary_field": self.primary_field,
            "fields": [f.to_dict() for f in self.fields],
            "webhook_path": self.webhook_path,
            "default_label": self.default_label or f"{self.label} connection",
            "description": self.description,
        }


def _f(id: str, label: str, **kw: Any) -> ChannelCredentialField:
    return ChannelCredentialField(id=id, label=label, **kw)


# Schema per channel — exactly the fields each transport needs. Secret fields are
# masked in the UI and never returned in plaintext.
CHANNEL_CREDENTIAL_SPECS: dict[str, ChannelCredentialSpec] = {
    "telegram": ChannelCredentialSpec(
        channel_id="telegram",
        label="Telegram",
        primary_field="token",
        webhook_path="/api/v1/channels/telegram/webhook",
        fields=(_f("token", "Bot token", placeholder="123456:ABC-DEF…"),),
    ),
    "slack": ChannelCredentialSpec(
        channel_id="slack",
        label="Slack",
        primary_field="bot_token",
        webhook_path="/api/v1/channels/slack/events",
        fields=(
            _f("bot_token", "Bot token", placeholder="xoxb-…"),
            _f("signing_secret", "Signing secret", placeholder="Slack signing secret"),
        ),
    ),
    "discord": ChannelCredentialSpec(
        channel_id="discord",
        label="Discord",
        primary_field="bot_token",
        webhook_path="/api/v1/channels/discord/interactions",
        fields=(
            _f("bot_token", "Bot token", placeholder="Discord bot token"),
            _f("public_key", "Public key (Ed25519)", secret=False, required=False, placeholder="hex public key"),
            _f("application_id", "Application ID", secret=False, required=False, placeholder="numeric app id"),
        ),
    ),
    "whatsapp": ChannelCredentialSpec(
        channel_id="whatsapp",
        label="WhatsApp",
        primary_field="access_token",
        webhook_path="/api/v1/channels/whatsapp/webhook",
        fields=(
            _f("access_token", "Access token", placeholder="Meta WhatsApp access token"),
            _f("phone_number_id", "Phone number ID", secret=False, placeholder="numeric phone number id"),
            _f("verify_token", "Webhook verify token", secret=False, required=False, placeholder="your verify token"),
            _f("app_secret", "App secret", required=False, placeholder="Meta app secret (verifies inbound)"),
        ),
    ),
    "messenger": ChannelCredentialSpec(
        channel_id="messenger",
        label="Messenger",
        primary_field="page_access_token",
        webhook_path="/api/v1/channels/messenger/webhook",
        fields=(
            _f("page_access_token", "Page access token", placeholder="Meta Page access token"),
            _f("verify_token", "Webhook verify token", secret=False, required=False, placeholder="your verify token"),
            _f("app_secret", "App secret", required=False, placeholder="Meta app secret"),
        ),
    ),
    "matrix": ChannelCredentialSpec(
        channel_id="matrix",
        label="Matrix",
        primary_field="access_token",
        fields=(
            _f("homeserver_url", "Homeserver URL", secret=False, placeholder="https://matrix.org"),
            _f("access_token", "Access token", placeholder="Matrix access token"),
        ),
    ),
    "teams": ChannelCredentialSpec(
        channel_id="teams",
        label="Microsoft Teams",
        primary_field="webhook_url",
        fields=(_f("webhook_url", "Incoming webhook URL", placeholder="https://outlook.office.com/webhook/…"),),
    ),
    "sms": ChannelCredentialSpec(
        channel_id="sms",
        label="SMS",
        primary_field="auth_token",
        fields=(
            _f("account_sid", "Twilio Account SID", secret=False, placeholder="AC…"),
            _f("auth_token", "Twilio auth token", placeholder="Twilio auth token"),
            _f("from_number", "From number", secret=False, placeholder="+1…"),
        ),
    ),
}


def get_channel_credential_spec(channel_id: str) -> ChannelCredentialSpec | None:
    return CHANNEL_CREDENTIAL_SPECS.get((channel_id or "").strip().lower())


def channel_supports_credentials(channel_id: str) -> bool:
    """A channel is connectable from the UI only if it has a schema AND a
    registered adapter (never a credential box for an unimplemented adapter)."""
    if get_channel_credential_spec(channel_id) is None:
        return False
    try:
        from aethos_core.channels.channel_registry import get_channel_adapter

        return get_channel_adapter(channel_id) is not None
    except Exception:
        return False


class ChannelCredentialError(ValueError):
    """Raised when a channel credential payload is invalid."""


def store_channel_credentials(*, channel_id: str, label: str, fields: dict[str, str]) -> Any:
    """Validate and store a channel's credentials in the vault as one JSON blob."""
    spec = get_channel_credential_spec(channel_id)
    if spec is None:
        raise ChannelCredentialError(f"Unknown channel: {channel_id}")
    cleaned: dict[str, str] = {}
    for f in spec.fields:
        value = str(fields.get(f.id) or "").strip()
        if f.required and not value:
            raise ChannelCredentialError(f"{f.label} is required.")
        if value:
            cleaned[f.id] = value
    primary = cleaned.get(spec.primary_field, "")
    if not primary:
        raise ChannelCredentialError(f"{spec.label} requires its primary credential.")
    blob = json.dumps(cleaned, separators=(",", ":"))
    record = get_credential_vault().store_api_token(
        provider=spec.channel_id,
        label=(label or spec.default_label or f"{spec.label} connection").strip(),
        token=blob,
        scope=["channel_send", "channel_receive"],
        write_allowed=False,
        masked_identifier=mask_secret(primary, visible=4),
    )
    return record


def _parse_secret(raw: str) -> dict[str, str]:
    raw = (raw or "").strip()
    if not raw:
        return {}
    if raw.startswith("{"):
        try:
            parsed = json.loads(raw)
            return {str(k): str(v) for k, v in parsed.items()} if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    # Telegram-style plain token (back-compat).
    return {"token": raw}


def resolve_channel_credentials(channel_id: str) -> dict[str, str]:
    """Return the most recent non-revoked vault credential fields for a channel.

    Empty dict when none stored. Reads Telegram's existing plain-token creds too.
    """
    spec = get_channel_credential_spec(channel_id)
    provider = spec.channel_id if spec else (channel_id or "").strip().lower()
    vault = get_credential_vault()
    creds = [c for c in vault.list_credentials(provider=provider) if not c.revoked]
    if not creds:
        return {}
    creds.sort(key=lambda c: (c.last_used_at or c.created_at or 0), reverse=True)
    for cred in creds:
        fields = _parse_secret(str((vault.retrieve_secret(cred.credential_id) or {}).get("token") or ""))
        if fields:
            return fields
    return {}


def channel_runtime_enabled(channel_id: str, env_enabled: bool) -> bool:
    """A channel is live when its env flag is on OR vault credentials are stored —
    so connecting from the UI needs no .env editing."""
    return bool(env_enabled or channel_has_vault_credentials(channel_id))


def channel_field(channel_id: str, field_id: str, env_fallback: str = "") -> str:
    """Resolve a single channel field: vault first, then env/.env fallback."""
    value = str(resolve_channel_credentials(channel_id).get(field_id) or "").strip()
    return value or str(env_fallback or "").strip()


def channel_has_vault_credentials(channel_id: str) -> bool:
    spec = get_channel_credential_spec(channel_id)
    if spec is None:
        return False
    fields = resolve_channel_credentials(channel_id)
    # Telegram plain token maps to its single primary field.
    if spec.channel_id == "telegram":
        return bool(fields.get("token"))
    return bool(fields.get(spec.primary_field))


def list_channel_credentials(channel_id: str) -> list[dict[str, Any]]:
    spec = get_channel_credential_spec(channel_id)
    provider = spec.channel_id if spec else (channel_id or "").strip().lower()
    return [c.to_public_dict() for c in get_credential_vault().list_credentials(provider=provider) if not c.revoked]


def test_channel_credential(channel_id: str, credential_id: str) -> dict[str, Any]:
    vault = get_credential_vault()
    rec = vault.get(credential_id)
    spec = get_channel_credential_spec(channel_id)
    provider = spec.channel_id if spec else (channel_id or "").strip().lower()
    if not rec or rec.provider != provider:
        raise KeyError(credential_id)
    fields = _parse_secret(str((vault.retrieve_secret(credential_id) or {}).get("token") or ""))
    if not fields:
        return {"ok": False, "detail": "Credential secret missing or not decryptable."}
    primary = spec.primary_field if spec else "token"
    if not fields.get(primary):
        return {"ok": False, "detail": "Primary credential missing."}
    return {"ok": True, "detail": f"{(spec.label if spec else channel_id)} credentials stored and decryptable."}


def revoke_channel_credential(channel_id: str, credential_id: str) -> bool:
    vault = get_credential_vault()
    rec = vault.get(credential_id)
    spec = get_channel_credential_spec(channel_id)
    provider = spec.channel_id if spec else (channel_id or "").strip().lower()
    if not rec or rec.provider != provider:
        return False
    return vault.revoke(credential_id)


def channel_connection_payload(channel_id: str) -> dict[str, Any]:
    from aethos_core.security.credential_vault import get_credential_vault_diagnostics

    spec = get_channel_credential_spec(channel_id)
    return {
        "ok": True,
        "channel": channel_id,
        "supports_credentials": channel_supports_credentials(channel_id),
        "schema": spec.to_schema() if spec else None,
        "configured": channel_has_vault_credentials(channel_id),
        "credentials": list_channel_credentials(channel_id),
        "webhook_path": spec.webhook_path if spec else None,
        "credential_vault": get_credential_vault_diagnostics(),
    }
