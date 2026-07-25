# SPDX-License-Identifier: Apache-2.0
"""Cross-provider correlation engine."""

from __future__ import annotations

from typing import Any

_DOMAINS = ("railway", "github", "vercel", "browser", "engineering", "workspace", "presence", "research")


def correlate_operational_signals(*, events: list[dict[str, Any]] | None = None, anomalies: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Correlate signals across operational domains."""
    rows = list(events or [])
    domain_hits: dict[str, int] = {d: 0 for d in _DOMAINS}
    correlations: list[dict[str, Any]] = []

    for event in rows:
        text = f"{event.get('source')} {event.get('summary')} {event.get('category')} {event.get('provider')}".lower()
        for domain in _DOMAINS:
            if domain in text or (domain == "github" and "workflow" in text):
                domain_hits[domain] += 1

    active = [d for d, c in domain_hits.items() if c > 0]
    if "github" in active and ("railway" in active or "vercel" in active):
        correlations.append(
            {
                "pattern": "workflow_to_deployment",
                "domains": ["github", "railway" if "railway" in active else "vercel"],
                "summary": "GitHub workflow instability correlated with deployment delays.",
            }
        )
    if ("railway" in active or "vercel" in active) and "browser" in active:
        correlations.append(
            {
                "pattern": "deployment_to_browser",
                "domains": ["railway" if "railway" in active else "vercel", "browser"],
                "summary": "Deployment instability correlated with stale browser evidence.",
            }
        )
    if len(active) >= 3:
        correlations.append(
            {
                "pattern": "multi_domain_instability",
                "domains": active[:4],
                "summary": f"Cross-domain instability across {', '.join(active[:4])}.",
            }
        )

    for anomaly in anomalies or []:
        kind = str(anomaly.get("kind") or "")
        if "workflow" in kind and "deployment" in kind:
            correlations.append(
                {
                    "pattern": "workflow_deployment_cascade",
                    "domains": ["github", "railway"],
                    "summary": "Workflow instability and deployment failures co-occurring.",
                }
            )

    strength = min(1.0, len(correlations) * 0.25 + len(active) * 0.08)
    return {
        "correlations": correlations[:6],
        "active_domains": active,
        "domain_hits": domain_hits,
        "correlation_strength": round(strength, 2),
        "readonly": True,
    }
