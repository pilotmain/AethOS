# SPDX-License-Identifier: Apache-2.0
"""Route integrity — verifies mounted APIs."""

from __future__ import annotations

from typing import Any

from aethos_core.human_centered.human_route_registry import discover_human_routes


def verify_human_route_integrity(*, app: Any | None = None) -> dict[str, Any]:
    discovery = discover_human_routes(app=app)
    return {
        "ok": discovery.get("health") == "healthy",
        "health": discovery.get("health"),
        "missing_routes": discovery.get("missing_routes") or [],
        "mounted_count": discovery.get("route_count", 0),
        "anomalies": [
            f"Human API {r.get('path')} missing" for r in (discovery.get("missing_routes") or [])
        ],
    }
