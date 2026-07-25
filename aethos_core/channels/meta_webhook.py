# SPDX-License-Identifier: Apache-2.0
"""Meta (WhatsApp Cloud / Messenger) webhook signature verification.

Meta signs every inbound webhook POST with `X-Hub-Signature-256: sha256=<hmac>`,
an HMAC-SHA256 of the raw request body keyed by the app secret. Verifying it stops
anyone who learns the public webhook URL from injecting forged inbound messages.

Mirrors the Slack/Discord signature pattern already used in this codebase: when an
app secret is configured the signature is enforced; when it isn't, verification is
skipped so the operator can still complete the Meta setup handshake before pasting
the secret (the channel is still gated by enabled-state + verify_token).
"""

from __future__ import annotations

import hashlib
import hmac


def verify_meta_signature(*, body: bytes, signature: str, app_secret: str) -> bool:
    """True when `signature` is a valid sha256 HMAC of `body` under `app_secret`."""
    secret = (app_secret or "").strip()
    sig = (signature or "").strip()
    if not secret or not sig or not sig.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


def meta_app_secret(channel: str) -> str:
    """Resolve a channel's Meta app secret: vault first, then env/.env fallback."""
    from aethos_core.channels.channel_credentials import channel_field
    from aethos_core.config import get_settings

    env_fallback = str(getattr(get_settings(), f"{channel}_app_secret", "") or "")
    return channel_field(channel, "app_secret", env_fallback)
