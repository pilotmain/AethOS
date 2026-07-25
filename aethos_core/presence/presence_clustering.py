# SPDX-License-Identifier: Apache-2.0
"""Operational clustering — group related events into incidents."""

from __future__ import annotations

from time import time
from typing import Any
from uuid import uuid4

_CLUSTER_THEMES = (
    ("deployment_instability", ("deployment", "railway", "restart", "vercel", "rollout")),
    ("workflow_instability", ("workflow", "github", "rerun", "ci", "flaky_workflow")),
    ("browser_runtime", ("browser", "dns", "evidence failure")),
    ("dependency_risk", ("dependency", "cve", "churn")),
    ("engineering_validation", ("validation", "pytest", "preflight", "sandbox")),
)


def cluster_operational_signals(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group related operational events into incident clusters."""
    buckets: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        theme = _theme_for_event(event)
        buckets.setdefault(theme, []).append(event)

    clusters: list[dict[str, Any]] = []
    for theme, rows in buckets.items():
        if theme == "general" and len(rows) < 2:
            continue
        if len(rows) < 2 and theme == "internal_substrate":
            continue
        clusters.append(_build_cluster(theme, rows))
    clusters.sort(key=lambda c: float(c.get("confidence") or 0), reverse=True)
    return clusters


def list_operational_incidents(clusters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Incidents are clusters with operational significance."""
    return [c for c in clusters if c.get("theme") != "internal_substrate" and int(c.get("event_count") or 0) >= 2]


def _theme_for_event(event: dict[str, Any]) -> str:
    if str(event.get("signal_class") or "") == "internal_substrate":
        return "internal_substrate"
    text = f"{event.get('source')} {event.get('summary')}".lower()
    for theme, keys in _CLUSTER_THEMES:
        if any(k in text for k in keys):
            return theme
    return "general"


def _build_cluster(theme: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows.sort(key=lambda r: float(r.get("at") or r.get("created_at") or 0))
    sources = sorted({str(r.get("source") or "") for r in rows if r.get("source")})
    providers = sorted({str(r.get("provider") or "") for r in rows if r.get("provider")})
    confidence = min(0.45 + len(rows) * 0.08 + sum(float(r.get("confidence") or 0.5) for r in rows) / max(len(rows), 1) * 0.2, 0.92)
    title = _cluster_title(theme, len(rows))
    return {
        "cluster_id": f"pclust-{uuid4().hex[:10]}",
        "theme": theme,
        "title": title,
        "event_count": len(rows),
        "sources": sources,
        "providers": providers,
        "confidence": round(confidence, 2),
        "timeline": [{"at": r.get("at"), "summary": r.get("summary")} for r in rows[:8]],
        "related_systems": _systems_for_theme(theme),
        "created_at": time(),
    }


def _cluster_title(theme: str, count: int) -> str:
    titles = {
        "deployment_instability": "Potential deployment instability cluster",
        "workflow_instability": "GitHub workflow instability cluster",
        "browser_runtime": "Browser/runtime verification cluster",
        "dependency_risk": "Dependency risk cluster",
        "engineering_validation": "Engineering validation cluster",
        "internal_substrate": "Internal substrate scans",
    }
    base = titles.get(theme, "Operational signal cluster")
    return f"{base} ({count} signals)" if count > 1 else base


def _systems_for_theme(theme: str) -> list[str]:
    mapping = {
        "deployment_instability": ["Railway", "deployments", "CI"],
        "workflow_instability": ["GitHub Actions", "CI"],
        "browser_runtime": ["browser evidence", "deployments"],
        "dependency_risk": ["dependencies", "npm"],
        "engineering_validation": ["engineering", "validation"],
    }
    return mapping.get(theme, ["operations"])
