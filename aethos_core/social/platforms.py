# SPDX-License-Identifier: Apache-2.0
"""Supported social platforms and their capabilities — the single source of truth for the
social connector framework. Credentials live in the encrypted vault (provider = the platform
name), exactly like other providers; posting is approval-gated like any other mutation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SocialPlatform:
    name: str  # vault provider key + api id, e.g. "linkedin"
    label: str
    can_post: bool
    can_read: bool
    char_limit: int  # 0 = no hard limit
    api_key_url: str  # where the user creates an app / token


# Registry. `can_post`/`can_read` describe the INTENDED capability; the actual call is gated
# on a vault credential being present (connectors.social_platform_connected).
SOCIAL_PLATFORMS: dict[str, SocialPlatform] = {
    "x": SocialPlatform(
        name="x", label="X (Twitter)", can_post=True, can_read=True, char_limit=280,
        api_key_url="https://developer.x.com/en/portal/dashboard",
    ),
    "linkedin": SocialPlatform(
        name="linkedin", label="LinkedIn", can_post=True, can_read=True, char_limit=3000,
        api_key_url="https://www.linkedin.com/developers/apps",
    ),
    "facebook": SocialPlatform(
        name="facebook", label="Facebook", can_post=True, can_read=True, char_limit=0,
        api_key_url="https://developers.facebook.com/apps",
    ),
    "instagram": SocialPlatform(
        name="instagram", label="Instagram", can_post=True, can_read=True, char_limit=2200,
        api_key_url="https://developers.facebook.com/docs/instagram-api",
    ),
    "mastodon": SocialPlatform(
        name="mastodon", label="Mastodon", can_post=True, can_read=True, char_limit=500,
        api_key_url="https://docs.joinmastodon.org/client/token/",
    ),
    "threads": SocialPlatform(
        name="threads", label="Threads", can_post=True, can_read=True, char_limit=500,
        api_key_url="https://developers.facebook.com/docs/threads",
    ),
}

# Aliases people type so "twitter" resolves to "x", etc.
_ALIASES = {"twitter": "x", "x.com": "x", "ig": "instagram", "insta": "instagram", "fb": "facebook", "li": "linkedin"}


def normalize_platform(name: str) -> str:
    key = (name or "").strip().lower()
    return _ALIASES.get(key, key)


def platform_spec(name: str) -> SocialPlatform | None:
    return SOCIAL_PLATFORMS.get(normalize_platform(name))


def supported_platform_names() -> list[str]:
    return list(SOCIAL_PLATFORMS.keys())
