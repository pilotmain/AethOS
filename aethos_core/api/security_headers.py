# SPDX-License-Identifier: Apache-2.0
"""§5 Transport security headers middleware.

Adds the standard app-layer security headers to every API response:

  * ``Content-Security-Policy`` (with ``frame-ancestors 'none'``)
  * ``Strict-Transport-Security`` (HSTS — honored only over HTTPS)
  * ``X-Content-Type-Options: nosniff``
  * ``X-Frame-Options: DENY``
  * ``Referrer-Policy``
  * ``Permissions-Policy``
  * ``X-Permitted-Cross-Domain-Policies: none``

A TLS-terminating reverse proxy is required for any non-localhost deploy (HSTS
is meaningless without HTTPS); see SECURITY.md. CSP is relaxed on the interactive
docs routes so Swagger UI / Redoc keep functioning.
"""

from __future__ import annotations

from starlette.responses import Response

# Docs UIs need inline scripts + a CDN; keep them working with a scoped CSP.
_DOCS_PREFIXES = ("/docs", "/redoc")
_DOCS_CSP = (
    "default-src 'self'; img-src 'self' data: https:; "
    "style-src 'self' 'unsafe-inline' https:; script-src 'self' 'unsafe-inline' https:; "
    "connect-src 'self'; frame-ancestors 'none'"
)


async def security_headers_middleware(request, call_next) -> Response:
    from aethos_core.config import get_settings

    s = get_settings()
    response = await call_next(request)
    if not s.security_headers_enabled:
        return response

    path = request.url.path
    is_docs = any(path.startswith(p) for p in _DOCS_PREFIXES)
    headers = response.headers
    headers.setdefault("Content-Security-Policy", _DOCS_CSP if is_docs else s.security_headers_csp)
    headers.setdefault("X-Content-Type-Options", "nosniff")
    headers.setdefault("X-Frame-Options", "DENY")
    headers.setdefault("Referrer-Policy", s.security_headers_referrer_policy)
    headers.setdefault("Permissions-Policy", s.security_headers_permissions_policy)
    headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")
    if s.security_headers_hsts_enabled:
        headers.setdefault(
            "Strict-Transport-Security",
            f"max-age={s.security_headers_hsts_max_age}; includeSubDomains; preload",
        )
    return response
