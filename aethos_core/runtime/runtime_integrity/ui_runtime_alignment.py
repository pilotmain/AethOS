# SPDX-License-Identifier: Apache-2.0
"""UI ↔ backend alignment — frontend view parity with API routes."""

from __future__ import annotations

from typing import Any

from aethos_core.human_centered.human_route_registry import UI_HUMAN_VIEW_ALIGNMENT, discover_human_routes


def verify_ui_runtime_alignment(*, app: Any | None = None) -> dict[str, Any]:
    discovery = discover_human_routes(app=app)
    mounted_paths = {r["path"] for r in discovery.get("mounted_routes") or [] if r.get("mounted")}

    aligned: list[dict[str, str]] = []
    misaligned: list[dict[str, str]] = []

    for item in UI_HUMAN_VIEW_ALIGNMENT:
        endpoint = item["endpoint"]
        if endpoint in mounted_paths:
            aligned.append({**item, "status": "aligned"})
        else:
            misaligned.append({**item, "status": "missing_backend", "detail": f"{endpoint} not mounted"})

    health = "healthy" if not misaligned else "degraded"
    return {
        "ok": not misaligned,
        "health": health,
        "aligned": aligned,
        "misaligned": misaligned,
        "anomalies": [
            f"Living Intelligence UI {m['view']} mounted without backend {m['endpoint']}"
            for m in misaligned
        ],
    }
