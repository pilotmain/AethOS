# SPDX-License-Identifier: Apache-2.0
"""Classify Vercel URLs — production vs preview vs custom domain."""

from __future__ import annotations

import re
from urllib.parse import urlparse

UrlType = str  # custom_domain | production_vercel | preview_vercel | unknown

_HASH_SEGMENT_RX = re.compile(r"^[a-z0-9]{6,12}$", re.I)


def _looks_like_deploy_hash(part: str) -> bool:
    """Vercel preview hosts embed random hash segments (usually include digits)."""
    return bool(_HASH_SEGMENT_RX.fullmatch(part)) and any(ch.isdigit() for ch in part)
_TEAM_PREVIEW_RX = re.compile(r"-[a-z0-9]+-(?:[a-z0-9-]+-)?projects\.vercel\.app$", re.I)


def _host_from_url(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def classify_url_type(url: str | None) -> UrlType:
    """
    custom_domain — non-vercel.app production-style domain
    production_vercel — {project}.vercel.app style
    preview_vercel — deployment hash / team preview hostnames
    """
    raw = (url or "").strip()
    if not raw:
        return "unknown"
    host = _host_from_url(raw)
    if not host:
        return "unknown"
    if not host.endswith(".vercel.app"):
        return "custom_domain"

    if _TEAM_PREVIEW_RX.search(host):
        return "preview_vercel"

    slug = host[: -len(".vercel.app")]
    parts = slug.split("-")
    if parts[-1] in ("projects", "project") and len(parts) >= 3:
        return "preview_vercel"

    hash_parts = [p for p in parts if _looks_like_deploy_hash(p)]
    if hash_parts:
        return "preview_vercel"

    if len(parts) >= 4:
        return "preview_vercel"

    if len(parts) <= 3 and all(len(p) <= 24 for p in parts):
        return "production_vercel"

    if slug.count("-") <= 1 and len(slug) <= 48:
        return "production_vercel"

    return "preview_vercel"


def is_production_confidence_url(url_type: UrlType) -> bool:
    return url_type in ("custom_domain", "production_vercel")


def url_type_rank(url_type: UrlType) -> int:
    """Lower is better when choosing a canonical production URL."""
    return {
        "custom_domain": 0,
        "production_vercel": 1,
        "preview_vercel": 2,
        "unknown": 3,
    }.get(url_type, 3)
