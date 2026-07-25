# SPDX-License-Identifier: Apache-2.0
"""Social connectors — connection state, governed publishing, and feed reads.

Tokens live in the encrypted vault (provider = platform name), tenant-scoped like every other
credential. Publishing is APPROVAL-GATED: publish_to_platform refuses unless approved=True, and
refuses (with a clear connect-hint) when no token is stored. Per-platform API calls are made with
httpx (no SDKs); platforms without a wired publisher return a clear, honest 'not wired yet'
instead of pretending to post. Nothing auto-posts.
"""

from __future__ import annotations

import logging
from typing import Any

from aethos_core.social.platforms import normalize_platform, platform_spec, supported_platform_names

_log = logging.getLogger("aethos.social")


def social_platform_connected(platform: str) -> bool:
    """True when a (non-revoked) credential for this platform exists in the current tenant's vault."""
    name = normalize_platform(platform)
    if not platform_spec(name):
        return False
    try:
        from aethos_core.security.credential_vault import get_credential_vault

        return any(not c.revoked for c in get_credential_vault().list_credentials(provider=name))
    except Exception:
        return False


def connected_platforms() -> list[str]:
    return [p for p in supported_platform_names() if social_platform_connected(p)]


def _resolve_token(platform: str) -> str | None:
    name = normalize_platform(platform)
    try:
        from aethos_core.security.credential_vault import get_credential_vault

        vault = get_credential_vault()
        for c in vault.list_credentials(provider=name):
            if c.revoked:
                continue
            secret = vault.retrieve_secret(c.credential_id)
            if secret and secret.get("token"):
                return str(secret["token"])
    except Exception:
        return None
    return None


def _connect_hint(platform: str) -> str:
    spec = platform_spec(platform)
    label = spec.label if spec else platform
    return (
        f"{label} isn't connected. Add a {label} API token in "
        f"Mission Control → Advanced settings → Credentials (provider: {normalize_platform(platform)})."
    )


def publish_to_platform(platform: str, text: str, *, approved: bool = False) -> dict[str, Any]:
    """Governed publish. Refuses unless explicitly approved AND connected. Never auto-posts."""
    name = normalize_platform(platform)
    spec = platform_spec(name)
    if not spec or not spec.can_post:
        return {"ok": False, "error": "unsupported_platform", "platform": name}
    if not text or not text.strip():
        return {"ok": False, "error": "empty_post"}
    if spec.char_limit and len(text) > spec.char_limit:
        return {"ok": False, "error": "too_long", "limit": spec.char_limit, "length": len(text)}
    if not approved:
        # Approval gate — the same governance posture as deployments/mutations.
        return {"ok": False, "error": "approval_required",
                "detail": f"Posting to {spec.label} needs explicit approval before it goes out."}
    token = _resolve_token(name)
    if not token:
        return {"ok": False, "error": "not_connected", "detail": _connect_hint(name)}

    publisher = _PUBLISHERS.get(name)
    if publisher is None:
        return {"ok": False, "error": "publisher_not_wired",
                "detail": f"{spec.label} token is stored, but its publish API isn't wired yet."}
    return publisher(token, text)


def read_recent(platform: str, *, limit: int = 5) -> dict[str, Any]:
    """Read recent items from a connected platform (gated). Reader wiring is per-platform."""
    name = normalize_platform(platform)
    spec = platform_spec(name)
    if not spec or not spec.can_read:
        return {"ok": False, "error": "unsupported_platform", "platform": name}
    if not social_platform_connected(name):
        return {"ok": False, "error": "not_connected", "detail": _connect_hint(name)}
    reader = _READERS.get(name)
    if reader is None:
        return {"ok": False, "error": "reader_not_wired", "detail": f"{spec.label} feed read isn't wired yet."}
    return reader(_resolve_token(name) or "", limit)


# ───────────────────────── per-platform publishers (httpx, no SDK) ─────────────────────────


def _publish_x(token: str, text: str) -> dict[str, Any]:
    """Post a tweet via X API v2 (OAuth2 user token with tweet.write)."""
    import httpx

    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(
                "https://api.twitter.com/2/tweets",
                json={"text": text},
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            )
    except httpx.HTTPError as exc:
        return {"ok": False, "error": "platform_unreachable", "detail": exc.__class__.__name__}
    if resp.status_code >= 400:
        return {"ok": False, "error": "platform_error", "status_code": resp.status_code,
                "detail": (resp.text or "")[:200]}
    data = resp.json()
    post_id = str((data.get("data") or {}).get("id") or "")
    return {"ok": True, "platform": "x", "post_id": post_id, "published": True}


def _publish_mastodon(token: str, text: str) -> dict[str, Any]:
    """Post a status via the Mastodon API. Requires MASTODON_BASE_URL for the instance."""
    import httpx

    from aethos_core.config import get_settings

    base = str(getattr(get_settings(), "mastodon_base_url", "") or "").strip().rstrip("/")
    if not base:
        return {"ok": False, "error": "mastodon_instance_not_set", "detail": "Set MASTODON_BASE_URL."}
    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(
                f"{base}/api/v1/statuses",
                data={"status": text},
                headers={"Authorization": f"Bearer {token}"},
            )
    except httpx.HTTPError as exc:
        return {"ok": False, "error": "platform_unreachable", "detail": exc.__class__.__name__}
    if resp.status_code >= 400:
        return {"ok": False, "error": "platform_error", "status_code": resp.status_code}
    return {"ok": True, "platform": "mastodon", "post_id": str(resp.json().get("id") or ""), "published": True}


# LinkedIn / Facebook / Instagram / Threads need account-id + OAuth-scope specifics that vary by
# app; their publishers are intentionally left unwired until app credentials exist (publish returns
# 'publisher_not_wired' — honest, never a fake post). X and Mastodon are wired.
_PUBLISHERS = {
    "x": _publish_x,
    "mastodon": _publish_mastodon,
}
_READERS: dict[str, Any] = {}
