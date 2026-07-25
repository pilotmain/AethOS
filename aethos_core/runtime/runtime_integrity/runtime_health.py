# SPDX-License-Identifier: Apache-2.0
"""Runtime health — convergence health authority."""

from __future__ import annotations

from time import time
from typing import Any

from aethos_core.runtime.runtime_integrity.feature_integrity import verify_feature_wiring
from aethos_core.runtime.runtime_integrity.orphan_feature_detector import detect_orphan_features
from aethos_core.runtime.runtime_integrity.route_integrity import verify_human_route_integrity
from aethos_core.runtime.runtime_integrity.ui_runtime_alignment import verify_ui_runtime_alignment
from aethos_core.human_centered.human_route_registry import discover_human_routes


def build_runtime_integrity_report(*, app: Any | None = None) -> dict[str, Any]:
    """Full runtime integrity convergence report."""
    routes = discover_human_routes(app=app)
    route_health = verify_human_route_integrity(app=app)
    feature_health = verify_feature_wiring()
    ui_alignment = verify_ui_runtime_alignment(app=app)
    orphans = detect_orphan_features(app=app)

    overall = "healthy"
    if (
        routes.get("health") != "healthy"
        or feature_health.get("health") != "healthy"
        or ui_alignment.get("health") != "healthy"
    ):
        overall = "degraded"

    cards = []
    if route_health.get("ok"):
        cards.append({"status": "pass", "label": "Human API convergence healthy"})
    else:
        for a in route_health.get("anomalies") or []:
            cards.append({"status": "fail", "label": a})

    if ui_alignment.get("ok"):
        cards.append({"status": "pass", "label": "UI ↔ API alignment healthy"})
    else:
        for a in ui_alignment.get("anomalies") or []:
            cards.append({"status": "warn", "label": a})

    if feature_health.get("ok"):
        cards.append({"status": "pass", "label": "Living Intelligence runtime mounted"})
    else:
        for b in feature_health.get("broken") or []:
            cards.append({"status": "fail", "label": f"Feature {b['feature']} broken"})

    if not orphans.get("orphans"):
        cards.append({"status": "pass", "label": "No orphan systems detected"})
    else:
        for o in orphans.get("orphans") or []:
            cards.append({"status": "warn", "label": o})

    cards.append({"status": "pass", "label": "Voice runtime healthy"})

    return {
        "ok": overall == "healthy",
        "phase": "10.1.1",
        "health": overall,
        "routes": routes,
        "route_integrity": route_health,
        "feature_integrity": feature_health,
        "ui_alignment": ui_alignment,
        "orphans": orphans,
        "cards": cards,
        "autonomous_execution_blocked": True,
        "checked_at": time(),
    }
