# SPDX-License-Identifier: Apache-2.0
"""Discord runtime — config, status, and Ed25519 interaction signature checks.

Discord signs every HTTP interaction with Ed25519 over ``timestamp + body`` and
requires the endpoint to verify it (and reject bad signatures with 401) before it
will register the interactions URL. Mirrors Slack's signature gate so Discord
reaches Telegram/Slack parity: signed inbound, governed handling, outbound send.
"""

from __future__ import annotations

from typing import Any

from aethos_core.config import get_settings


def _discord_field(field_id: str, env_attr: str) -> str:
    from aethos_core.channels.channel_credentials import channel_field

    return channel_field("discord", field_id, str(getattr(get_settings(), env_attr, "") or ""))


def discord_configured() -> bool:
    from aethos_core.channels.channel_credentials import channel_has_vault_credentials

    if channel_has_vault_credentials("discord"):
        return True
    s = get_settings()
    return bool(s.discord_enabled and str(s.discord_bot_token or "").strip())


def discord_signature_enforced() -> bool:
    """True when a public key is set (vault or env) so we can verify signatures."""
    return bool(_discord_field("public_key", "discord_public_key"))


def verify_discord_signature(*, body: bytes, signature: str, timestamp: str) -> bool:
    """Verify a Discord interaction's Ed25519 signature.

    Returns False on any malformed input or verification failure. Uses
    ``cryptography`` (already a dependency for the credential vault).
    """
    public_key = _discord_field("public_key", "discord_public_key")
    if not public_key or not signature or not timestamp:
        return False
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key))
        message = timestamp.encode("utf-8") + body
        try:
            key.verify(bytes.fromhex(signature), message)
            return True
        except InvalidSignature:
            return False
    except Exception:  # noqa: BLE001 — malformed key/sig, missing dep → reject.
        return False


def discord_channel_status() -> dict[str, Any]:
    s = get_settings()
    return {
        "ok": True,
        "channel": "discord",
        "enabled": bool(s.discord_enabled),
        "configured": discord_configured(),
        "signature_verification": discord_signature_enforced(),
        "interactions_path": "/api/v1/channels/discord/interactions",
    }
