# SPDX-License-Identifier: Apache-2.0
"""§4 API rate limiting & abuse protection.

A small, dependency-free sliding-window limiter applied as ASGI middleware:

  * Keys requests by identity (signed session cookie if present, else client IP)
    so a single abusive caller can't exhaust the budget for everyone.
  * Classifies the path into a bucket (auth / mutation / chat / default) and
    applies that bucket's per-minute limit — auth endpoints get the tightest
    budget for brute-force resistance.
  * Enforces a hard request-body size cap (413 on oversize).
  * Returns 429 with ``Retry-After`` and ``X-RateLimit-*`` headers on breach.

In-memory per-process counters are sufficient for AethOS's single-node /
small-team deployment target; for horizontally-scaled deploys the same interface
can be backed by Redis. Loopback is exempt by default so local single-operator
use is never throttled.
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections import defaultdict, deque

from starlette.responses import JSONResponse, Response

_LOCK = threading.Lock()
_WINDOWS: dict[str, deque[float]] = defaultdict(deque)

_AUTH_MARKERS = (
    "/aethos-identity/login",
    "/aethos-identity/register",
    "/aethos-identity/verify-email",
    "/aethos-identity/resend-verification",
    "/aethos-identity/mailer-test",
    "/aethos-identity/sso",
    "/aethos-identity/mfa",
    "/onboarding/login",
)
_MUTATION_MARKERS = ("/mutations", "/mutation", "/execute", "/agents/spawn")
_CHAT_MARKERS = ("/chat",)
_LOOPBACK = {"127.0.0.1", "::1", "localhost", "testclient"}


def _client_ip(request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    client = request.client
    return client.host if client else "unknown"


def _identity(request) -> str:
    from aethos_core.config import get_settings

    cookie = request.cookies.get(get_settings().auth_session_cookie)
    if cookie:
        return "sess:" + hashlib.sha256(cookie.encode()).hexdigest()[:16]
    return "ip:" + _client_ip(request)


def _bucket(path: str) -> str:
    if any(m in path for m in _AUTH_MARKERS):
        return "auth"
    if any(m in path for m in _MUTATION_MARKERS):
        return "mutation"
    if any(m in path for m in _CHAT_MARKERS):
        return "chat"
    return "default"


def _limit_for(bucket: str) -> int:
    from aethos_core.config import get_settings

    s = get_settings()
    return {
        "auth": s.rate_limit_auth_per_min,
        "mutation": s.rate_limit_mutation_per_min,
        "chat": s.rate_limit_chat_per_min,
    }.get(bucket, s.rate_limit_default_per_min)


def _check(key: str, limit: int, window: int) -> tuple[bool, int, float]:
    """Return (allowed, remaining, reset_epoch)."""
    now = time.time()
    cutoff = now - window
    with _LOCK:
        dq = _WINDOWS[key]
        while dq and dq[0] < cutoff:
            dq.popleft()
        if len(dq) >= limit:
            reset = dq[0] + window
            return False, 0, reset
        dq.append(now)
        return True, max(0, limit - len(dq)), now + window


def reset_state() -> None:
    """Test helper — clear all counters."""
    with _LOCK:
        _WINDOWS.clear()


async def rate_limit_middleware(request, call_next) -> Response:
    from aethos_core.config import get_settings

    s = get_settings()
    if not s.rate_limit_enabled or request.method == "OPTIONS":
        return await call_next(request)

    # Request body size cap (cheap header check; streaming bodies still bounded
    # by the server, this rejects declared-oversize uploads early).
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > s.max_request_bytes:
        return JSONResponse(
            {"error": "request_too_large", "max_bytes": s.max_request_bytes},
            status_code=413,
        )

    ip = _client_ip(request)
    if s.rate_limit_exempt_loopback and ip in _LOOPBACK:
        return await call_next(request)

    bucket = _bucket(request.url.path)
    limit = _limit_for(bucket)
    key = f"{_identity(request)}|{bucket}"
    allowed, remaining, reset = _check(key, limit, s.rate_limit_window_sec)
    if not allowed:
        retry_after = max(1, int(reset - time.time()))
        return JSONResponse(
            {"error": "rate_limited", "bucket": bucket, "retry_after_sec": retry_after},
            status_code=429,
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(reset)),
            },
        )
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(int(reset))
    return response
