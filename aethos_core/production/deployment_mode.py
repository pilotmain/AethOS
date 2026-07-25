# SPDX-License-Identifier: Apache-2.0
"""Deployment-mode helpers — local vs hosted behavior gates."""

from __future__ import annotations

from urllib.parse import urlparse

_HOSTED_DEFAULT_API_BASE = "https://pilotmain.com/aethos-api"


def deployment_mode() -> str:
    from aethos_core.config import get_settings

    return str(get_settings().deployment_mode or "local").strip().lower()


def is_hosted_deployment() -> bool:
    """True on shared cloud deploys (Railway/Vercel container) — no operator laptop disk."""
    return deployment_mode() == "hosted"


def is_local_deployment() -> bool:
    return not is_hosted_deployment()


def _origin_from_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return ""


def resolve_public_api_base_url(request=None) -> str:
    """Canonical public API origin for channel webhooks (no trailing slash).

    Hosted pilotmain deploys resolve to ``https://pilotmain.com/aethos-api``.
    ``PUBLIC_APP_BASE_URL`` (web prefix) is expanded to the API prefix when needed.
    """
    from aethos_core.config import get_settings

    settings = get_settings()
    configured = str(settings.public_app_base_url or "").strip().rstrip("/")
    if configured:
        parsed = urlparse(configured)
        if parsed.scheme and parsed.netloc:
            path = (parsed.path or "").strip()
            if path.endswith("/aethos-api"):
                return configured
            origin = _origin_from_url(configured)
            if path.endswith("/aethos") or path == "/aethos":
                return f"{origin}/aethos-api"
            if origin and ("aethos-api" in path or path.endswith("-api")):
                return configured
            if origin:
                return f"{origin}/aethos-api"

    redirect = str(settings.oidc_redirect_url or "").strip().rstrip("/")
    if redirect:
        origin = _origin_from_url(redirect)
        if origin:
            return f"{origin}/aethos-api"

    if is_hosted_deployment():
        return _HOSTED_DEFAULT_API_BASE

    if request is not None:
        from aethos_core.auth.email_verification import public_app_origin

        origin = public_app_origin(request).rstrip("/")
        if origin:
            host = urlparse(origin).netloc.lower()
            if host == "pilotmain.com" or host.endswith(".pilotmain.com"):
                return f"{origin}/aethos-api"
            return origin

    return ""


def telegram_canonical_webhook_url(request=None) -> str:
    """Production Telegram webhook URL derived from the deployment public API origin."""
    base = resolve_public_api_base_url(request).rstrip("/")
    if not base:
        return ""
    return f"{base}/api/v1/channels/telegram/webhook"
