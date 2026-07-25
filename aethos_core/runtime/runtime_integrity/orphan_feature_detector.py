# SPDX-License-Identifier: Apache-2.0
"""Orphan feature detector — disconnected runtime systems."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime.runtime_integrity.feature_integrity import verify_feature_wiring
from aethos_core.runtime.runtime_integrity.route_integrity import verify_human_route_integrity
from aethos_core.runtime.runtime_integrity.ui_runtime_alignment import verify_ui_runtime_alignment


def detect_orphan_features(*, app: Any | None = None) -> dict[str, Any]:
    routes = verify_human_route_integrity(app=app)
    features = verify_feature_wiring()
    ui = verify_ui_runtime_alignment(app=app)

    orphans: list[str] = []
    orphans.extend(routes.get("anomalies") or [])
    orphans.extend(f"Feature {b['feature']} unwired: {b['reason']}" for b in features.get("broken") or [])
    orphans.extend(ui.get("anomalies") or [])

    return {
        "ok": not orphans,
        "orphans": orphans,
        "count": len(orphans),
        "health": "healthy" if not orphans else "degraded",
    }
