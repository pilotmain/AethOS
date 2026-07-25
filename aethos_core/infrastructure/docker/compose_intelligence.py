# SPDX-License-Identifier: Apache-2.0
"""Compose intelligence — docker-compose operational topology."""

from __future__ import annotations

from typing import Any


def analyze_compose_topology(*, runtime_snapshot: dict[str, Any], relationships: dict[str, Any]) -> dict[str, Any]:
    services = runtime_snapshot.get("compose_services") or runtime_snapshot.get("services") or []
    if not isinstance(services, list):
        services = []
    if not services:
        services = [c.get("name") for c in (runtime_snapshot.get("containers") or []) if isinstance(c, dict)]
    return {
        "service_count": len(services),
        "services": services,
        "dependency_count": relationships.get("dependency_count", 0),
        "topology_stable": len(services) > 0,
        "summary": f"Compose topology spans {len(services)} services with {relationships.get('dependency_count', 0)} dependencies.",
    }
