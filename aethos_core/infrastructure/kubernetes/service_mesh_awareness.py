# SPDX-License-Identifier: Apache-2.0
"""Service mesh awareness — inter-service relationships."""

from __future__ import annotations

from typing import Any


def assess_service_mesh(*, runtime_snapshot: dict[str, Any]) -> dict[str, Any]:
    services = runtime_snapshot.get("services") or []
    routes = runtime_snapshot.get("service_routes") or []
    if not isinstance(services, list):
        services = []
    if not isinstance(routes, list):
        routes = []
    routing_normalized = all(r.get("normalized", True) for r in routes if isinstance(r, dict)) if routes else True
    return {
        "service_count": len(services),
        "route_count": len(routes),
        "routing_normalized": routing_normalized,
        "summary": "Service routing normalized." if routing_normalized else "Service routing drift detected.",
    }
