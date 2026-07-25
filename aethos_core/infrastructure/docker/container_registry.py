# SPDX-License-Identifier: Apache-2.0
"""Container registry — container discovery + metadata."""

from __future__ import annotations

from typing import Any


def discover_containers(*, runtime_snapshot: dict[str, Any]) -> dict[str, Any]:
    containers = runtime_snapshot.get("containers") or []
    if not isinstance(containers, list):
        containers = []
    discovered = []
    for raw in containers:
        if not isinstance(raw, dict):
            continue
        discovered.append({
            "name": str(raw.get("name") or "unknown"),
            "image": str(raw.get("image") or ""),
            "status": str(raw.get("status") or "unknown"),
            "restart_count": int(raw.get("restart_count") or 0),
            "role": str(raw.get("role") or "runtime"),
        })
    return {
        "container_count": len(discovered),
        "containers": discovered,
        "summary": f"Discovered {len(discovered)} operational containers.",
    }
