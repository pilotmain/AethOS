# SPDX-License-Identifier: Apache-2.0
"""Human API route registry — convergence discovery and health."""

from __future__ import annotations

from typing import Any

REQUIRED_HUMAN_ROUTES: list[dict[str, str]] = [
    {"path": "/human/overview", "method": "GET", "purpose": "convergence summary"},
    {"path": "/human/living", "method": "GET", "purpose": "living companion state"},
    {"path": "/human/live-presence", "method": "GET", "purpose": "realtime presence"},
    {"path": "/human/conversation", "method": "GET", "purpose": "continuity"},
    {"path": "/human/copilot", "method": "GET", "purpose": "operational copilot"},
    {"path": "/human/personal", "method": "GET", "purpose": "personal intelligence"},
    {"path": "/human/teamwork", "method": "GET", "purpose": "collaboration"},
    {"path": "/human/explainability", "method": "GET", "purpose": "trust reasoning"},
    {"path": "/human/thinking-boundaries", "method": "GET", "purpose": "governance"},
    {"path": "/human/multimodal-voice", "method": "GET", "purpose": "voice runtime"},
    {"path": "/human/routes", "method": "GET", "purpose": "endpoint discovery"},
    {"path": "/human/integrity", "method": "GET", "purpose": "runtime integrity report"},
    {"path": "/human/replay", "method": "GET", "purpose": "human runtime replay"},
    {"path": "/human/continuity", "method": "GET", "purpose": "continuity memory and resume"},
    {"path": "/human/trust-controls", "method": "GET", "purpose": "operator trust controls"},
    {"path": "/human/intuition", "method": "GET", "purpose": "operational intuition"},
    {"path": "/human/companion-brief", "method": "GET", "purpose": "calm companion brief"},
    {"path": "/human/presence-quality", "method": "GET", "purpose": "presence quality metrics"},
    {"path": "/human/calm-presence", "method": "GET", "purpose": "interruption budget and quiet mode"},
    {"path": "/human/timeline", "method": "GET", "purpose": "operational narrative"},
    {"path": "/human/living-explainability", "method": "GET", "purpose": "living explainability"},
    {"path": "/human/restraint", "method": "GET", "purpose": "intelligence restraint status"},
    {"path": "/human/partner-brief", "method": "GET", "purpose": "operational partner brief"},
    {"path": "/human/operational-reasoning", "method": "GET", "purpose": "deep operational reasoning"},
    {"path": "/human/investigation-companion", "method": "GET", "purpose": "investigation collaboration"},
    {"path": "/human/deep-replay", "method": "GET", "purpose": "deep replay intelligence"},
    {"path": "/human/emotional-realism", "method": "GET", "purpose": "emotional realism quality"},
    {"path": "/human/attention-awareness", "method": "GET", "purpose": "operator attention awareness"},
    {"path": "/human/companion-narrative", "method": "GET", "purpose": "companion narrative evolution"},
    {"path": "/human/companion-quality", "method": "GET", "purpose": "companion quality metrics v2"},
    {"path": "/human/restraint-v2", "method": "GET", "purpose": "intelligence restraint 2.0"},
]

# UI views that must align with backend routes (Mission Control)
UI_HUMAN_VIEW_ALIGNMENT: list[dict[str, str]] = [
    {"view": "human-living", "endpoint": "/human/living"},
    {"view": "human-live-presence", "endpoint": "/human/live-presence"},
    {"view": "human-conversation", "endpoint": "/human/conversation"},
    {"view": "human-copilot", "endpoint": "/human/copilot"},
    {"view": "human-personal", "endpoint": "/human/personal"},
    {"view": "human-teamwork", "endpoint": "/human/teamwork"},
    {"view": "human-explainability", "endpoint": "/human/explainability"},
    {"view": "human-thinking", "endpoint": "/human/thinking-boundaries"},
    {"view": "human-multimodal-voice", "endpoint": "/human/multimodal-voice"},
    {"view": "human-overview", "endpoint": "/human/overview"},
    {"view": "human-continuity", "endpoint": "/human/continuity"},
    {"view": "human-trust-controls", "endpoint": "/human/trust-controls"},
    {"view": "presence-attention-quality", "endpoint": "/human/intuition"},
    {"view": "presence-interruption-budget", "endpoint": "/human/calm-presence"},
    {"view": "presence-continuity-accuracy", "endpoint": "/human/continuity"},
    {"view": "presence-operational-narrative", "endpoint": "/human/timeline"},
    {"view": "presence-calm-intelligence", "endpoint": "/human/presence-quality"},
    {"view": "presence-trust-signals", "endpoint": "/human/living-explainability"},
    {"view": "presence-collaboration-quality", "endpoint": "/human/companion-brief"},
    {"view": "companion-operational-reasoning", "endpoint": "/human/operational-reasoning"},
    {"view": "companion-investigation", "endpoint": "/human/investigation-companion"},
    {"view": "companion-replay-intelligence", "endpoint": "/human/deep-replay"},
    {"view": "companion-emotional-realism", "endpoint": "/human/emotional-realism"},
    {"view": "companion-attention-awareness", "endpoint": "/human/attention-awareness"},
    {"view": "companion-narrative-evolution", "endpoint": "/human/companion-narrative"},
    {"view": "companion-trust-retention", "endpoint": "/human/companion-quality"},
]


def _normalize_route_path(path: str) -> str:
    if path.startswith("/api/v1"):
        return path[len("/api/v1") :]
    return path


def _collect_mounted_human_routes(app: Any) -> set[tuple[str, str]]:
    mounted: set[tuple[str, str]] = set()
    for route in getattr(app, "routes", []):
        path = _normalize_route_path(getattr(route, "path", "") or "")
        if not path.startswith("/human"):
            continue
        methods = getattr(route, "methods", None) or set()
        for method in methods:
            if method in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                mounted.add((path, method))
    return mounted


def discover_human_routes(*, app: Any | None = None) -> dict[str, Any]:
    """Discover mounted human API routes and report missing required endpoints."""
    if app is None:
        from aethos_core.api.main import app as fastapi_app

        app = fastapi_app

    mounted_raw = _collect_mounted_human_routes(app)
    mounted_routes: list[dict[str, str]] = []
    missing_routes: list[dict[str, str]] = []

    for spec in REQUIRED_HUMAN_ROUTES:
        path = spec["path"]
        method = spec["method"]
        entry = {**spec, "mounted": False}
        if (path, method) in mounted_raw:
            entry["mounted"] = True
            mounted_routes.append(entry)
        else:
            missing_routes.append(entry)

    # Include additional mounted human routes not in required list
    required_paths = {s["path"] for s in REQUIRED_HUMAN_ROUTES}
    for path, method in sorted(mounted_raw):
        if path not in required_paths and method == "GET":
            mounted_routes.append({"path": path, "method": method, "purpose": "extended", "mounted": True})

    health = "healthy" if not missing_routes else "degraded"
    return {
        "ok": True,
        "phase": "10.1.4",
        "mounted_routes": mounted_routes,
        "missing_routes": missing_routes,
        "health": health,
        "route_count": len(mounted_routes),
        "autonomous_execution_blocked": True,
    }
