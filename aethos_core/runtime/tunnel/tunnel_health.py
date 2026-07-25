# SPDX-License-Identifier: Apache-2.0
"""Tunnel health checks."""

from __future__ import annotations

from typing import Any

import httpx

from aethos_core.runtime.tunnel.tunnel_state import get_state


def check_tunnel_health() -> dict[str, Any]:
    state = get_state()
    public_url = state.get("public_url")
    if not public_url or state.get("status") != "running":
        return {"ok": False, "reachable": False, "detail": "tunnel not running"}
    try:
        with httpx.Client(timeout=8.0, follow_redirects=True) as client:
            r = client.get(str(public_url).rstrip("/") + "/")
        return {"ok": r.status_code < 500, "reachable": True, "status_code": r.status_code}
    except httpx.HTTPError as exc:
        return {"ok": False, "reachable": False, "detail": str(exc)[:200]}
