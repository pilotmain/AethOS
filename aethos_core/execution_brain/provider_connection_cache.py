# SPDX-License-Identifier: Apache-2.0
"""Short TTL cache for provider validate/discover/read ops — avoids repeated vault + API work.

Readonly provider questions ("show projects", "is it healthy", "logs for X") are asked
repeatedly in a session. Caching the result for a short TTL turns the second identical
query into a fast in-memory hit. A successful mutation to a provider invalidates that
provider's cached reads so the operator never sees stale state after a change (§C4).
"""

from __future__ import annotations

import time
from typing import Any

_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_DEFAULT_TTL_SEC = 25.0


def _key(provider: str, *, op: str, target: str = "") -> str:
    prov = (provider or "").strip().lower()
    tgt = (target or "").strip().lower()
    return f"{op}:{prov}:{tgt}" if tgt else f"{op}:{prov}"


def cache_get(provider: str, *, op: str = "validate", target: str = "") -> dict[str, Any] | None:
    key = _key(provider, op=op, target=target)
    row = _CACHE.get(key)
    if not row:
        return None
    expires_at, payload = row
    if time.time() > expires_at:
        _CACHE.pop(key, None)
        return None
    return dict(payload)


def cache_set(
    provider: str,
    payload: dict[str, Any],
    *,
    op: str = "validate",
    target: str = "",
    ttl_sec: float = _DEFAULT_TTL_SEC,
) -> None:
    key = _key(provider, op=op, target=target)
    _CACHE[key] = (time.time() + max(5.0, ttl_sec), dict(payload))


def cache_invalidate(provider: str, *, op: str | None = None) -> int:
    """Drop cached reads for a provider.

    With ``op`` given, drops only that op (all targets); otherwise drops every cached
    read for the provider. Returns the number of entries removed. Called after a
    successful mutation so subsequent reads reflect the change.
    """
    prov = (provider or "").strip().lower()
    if not prov:
        return 0
    prefix = f"{op}:{prov}" if op else None
    removed = 0
    for key in list(_CACHE.keys()):
        parts = key.split(":")
        if len(parts) < 2:
            continue
        key_op, key_prov = parts[0], parts[1]
        if key_prov != prov:
            continue
        if prefix is not None and key_op != op:
            continue
        _CACHE.pop(key, None)
        removed += 1
    return removed


def cache_clear_for_tests() -> None:
    _CACHE.clear()
