# SPDX-License-Identifier: Apache-2.0
"""Per-tenant abuse ceilings (Correction 4).

A tiny, dependency-free sliding-window limiter keyed by ``(scope, tenant)``. Used
for cost/DoS protection on expensive per-tenant operations (e.g. arbiter runs,
which fan out to many models per turn). The §4 HTTP middleware already throttles
per session/IP; this complements it with limits keyed by the resolved tenant at
the point of the expensive work.

In-memory per-process counters — sufficient for AethOS's single-node target; the
same interface can be backed by Redis for horizontally-scaled deploys.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from aethos_core.tenancy.tenant_context import DEFAULT_TENANT

_LOCK = threading.Lock()
_WINDOWS: dict[str, deque[float]] = defaultdict(deque)


def reset_for_tests() -> None:
    with _LOCK:
        _WINDOWS.clear()


def check_rate(scope: str, tenant: str, *, limit: int, window_sec: int) -> tuple[bool, int]:
    """Record an attempt; return (allowed, retry_after_sec).

    ``limit <= 0`` disables the limit (always allowed). When the window is full the
    attempt is *not* recorded and ``retry_after_sec`` is how long until the oldest
    entry ages out.
    """
    if limit <= 0:
        return True, 0
    now = time.time()
    cutoff = now - window_sec
    key = f"{scope}:{tenant}"
    with _LOCK:
        dq = _WINDOWS[key]
        while dq and dq[0] < cutoff:
            dq.popleft()
        if len(dq) >= limit:
            retry_after = max(1, int(dq[0] + window_sec - now))
            return False, retry_after
        dq.append(now)
        return True, 0


def check_arbiter_run(tenant: str) -> tuple[bool, int]:
    """Per-tenant arbiter-runs-per-hour ceiling. Operator/default tenant is exempt;
    no-op unless multi-tenancy is enabled."""
    from aethos_core.config import get_settings

    s = get_settings()
    if not s.multi_tenant_enabled or tenant == DEFAULT_TENANT:
        return True, 0
    return check_rate(
        "arbiter_run", tenant, limit=int(s.tenant_arbiter_runs_per_hour or 0), window_sec=3600
    )
