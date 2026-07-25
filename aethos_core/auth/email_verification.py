# SPDX-License-Identifier: Apache-2.0
"""Email verification policy for hosted self-signup."""

from __future__ import annotations

import logging
import secrets
import time
from typing import Any
from urllib.parse import urlparse

from aethos_core.production.deployment_mode import is_hosted_deployment

_log = logging.getLogger("aethos.auth.email_verification")

_HOSTED_DEFAULT_ORIGIN = "https://pilotmain.com"
_HOSTED_DEFAULT_BASE_PATH = "/aethos"


def email_verification_required() -> bool:
    """Hosted + self-signup must verify email before use."""
    from aethos_core.config import get_settings

    s = get_settings()
    if not s.auth_self_signup_enabled:
        return False
    if is_hosted_deployment():
        return True
    return False


def new_verification_token() -> tuple[str, float]:
    token = secrets.token_urlsafe(32)
    from aethos_core.config import get_settings

    ttl = int(getattr(get_settings(), "auth_verification_ttl_sec", 86400) or 86400)
    expires = time.time() + max(300, ttl)
    return token, expires


def user_email_verified(user: dict[str, Any]) -> bool:
    if str(user.get("auth") or "") == "sso":
        return True
    if not email_verification_required():
        return True
    if "email_verified" not in user:
        return True
    return bool(user.get("email_verified"))


def _configured_public_url() -> str:
    from aethos_core.config import get_settings

    return str(get_settings().public_app_base_url or "").strip().rstrip("/")


def _origin_from_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return ""


def _normalized_base_path_from_url(url: str) -> str:
    parsed = urlparse(url)
    path = (parsed.path or "").strip()
    if not path or path == "/":
        return ""
    return "/" + path.strip("/")


def _request_forwarded_host(request) -> str:
    return (
        str(request.headers.get("x-forwarded-host") or request.headers.get("host") or "localhost")
        .split(",")[0]
        .strip()
    )


def _request_forwarded_proto(request) -> str:
    return str(request.headers.get("x-forwarded-proto") or "https").split(",")[0].strip()


def public_app_origin(request) -> str:
    """scheme://host only — never includes a path prefix."""
    configured = _configured_public_url()
    if configured:
        origin = _origin_from_url(configured)
        if origin:
            return origin

    from aethos_core.config import get_settings

    redirect = str(get_settings().oidc_redirect_url or "").strip()
    if redirect:
        origin = _origin_from_url(redirect)
        if origin:
            return origin

    proto = _request_forwarded_proto(request)
    host = _request_forwarded_host(request)
    host_lower = host.lower()

    if is_hosted_deployment() and ("localhost" in host_lower or "127.0.0.1" in host_lower):
        _log.warning(
            "public_app_origin on hosted resolved to non-local default — set PUBLIC_APP_BASE_URL"
        )
        return _HOSTED_DEFAULT_ORIGIN

    return f"{proto}://{host}"


def public_app_base_path(request) -> str:
    """Single web base path (e.g. /aethos) from ONE source — no trailing slash."""
    configured = _configured_public_url()
    if configured:
        prefix = _normalized_base_path_from_url(configured)
        if prefix:
            return prefix
        # PUBLIC_APP_BASE_URL set to a bare origin (e.g. https://pilotmain.com) carries
        # no path — do NOT assume root, or hosted verify links drop the /aethos base
        # path and 404. Fall through to the hosted default below.

    from aethos_core.config import get_settings

    redirect = str(get_settings().oidc_redirect_url or "").strip()
    if redirect:
        prefix = _normalized_base_path_from_url(redirect)
        if prefix:
            return prefix

    if is_hosted_deployment():
        host_lower = _request_forwarded_host(request).lower()
        req_path = ""
        try:
            req_path = str(request.url.path or "")
        except Exception:  # noqa: BLE001
            pass
        if host_lower == "pilotmain.com" or host_lower.endswith(".pilotmain.com"):
            return _HOSTED_DEFAULT_BASE_PATH
        if "aethos-api" in req_path:
            return _HOSTED_DEFAULT_BASE_PATH
        return _HOSTED_DEFAULT_BASE_PATH

    return ""


def public_app_base(request) -> str:
    """Origin + optional path prefix for public web routes."""
    origin = public_app_origin(request)
    base_path = public_app_base_path(request)
    return f"{origin}{base_path}" if base_path else origin


def public_app_url(request, relative_path: str) -> str:
    """Build a public web URL with the base path applied exactly once."""
    rel = (relative_path or "").strip()
    if not rel.startswith("/"):
        rel = f"/{rel}"
    origin = public_app_origin(request)
    base_path = public_app_base_path(request)
    url = f"{origin}{base_path}{rel}"
    if base_path:
        url = url.replace(f"{base_path}{base_path}/", f"{base_path}/")
        url = url.replace(f"{base_path}{base_path}", base_path)
    return url


def verification_landing_path(request=None) -> str:
    """Relative path to the public verify-email page (base path included once)."""
    if request is not None:
        base_path = public_app_base_path(request)
    else:
        configured = _configured_public_url()
        if configured:
            base_path = _normalized_base_path_from_url(configured)
        elif is_hosted_deployment():
            base_path = _HOSTED_DEFAULT_BASE_PATH
        else:
            base_path = ""
    return f"{base_path}/verify-email" if base_path else "/verify-email"


def build_verification_url(request, token: str) -> str:
    origin = public_app_origin(request)
    base_path = public_app_base_path(request)
    landing = f"{origin}{base_path}/verify-email"
    if base_path:
        landing = landing.replace(f"{base_path}{base_path}/", f"{base_path}/")
        landing = landing.replace(f"{base_path}{base_path}", base_path)
    tok = (token or "").strip()
    sep = "&" if "?" in landing else "?"
    return f"{landing}{sep}token={tok}"


def compose_verification_email(*, verify_url: str, name: str = "") -> tuple[str, str]:
    who = name.strip() or "there"
    subject = "Verify your AethOS account"
    body = (
        f"Hi {who},\n\n"
        "Thanks for signing up for AethOS. Confirm your email to activate your account:\n\n"
        f"{verify_url}\n\n"
        "This link expires in 24 hours. If you didn't request this, you can ignore this email.\n\n"
        "— AethOS"
    )
    return subject, body
