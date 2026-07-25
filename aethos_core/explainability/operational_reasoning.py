# SPDX-License-Identifier: Apache-2.0
"""Operational reasoning — why attention increased."""

from __future__ import annotations

from typing import Any


def explain_attention_change(*, event: dict[str, Any], cluster: dict[str, Any] | None = None) -> str:
    parts = [f"Severity {event.get('priority', 'NOTICE')} because:"]
    if int(event.get("recurrence") or event.get("dedupe_count") or 1) > 1:
        parts.append(f"- {event.get('recurrence') or event.get('dedupe_count')} correlated signals")
    if event.get("operational_impact"):
        parts.append("- Operational impact flagged")
    if cluster:
        parts.append(f"- Cluster: {cluster.get('title', 'related incident')}")
    summary = str(event.get("summary") or "").lower()
    if "stale" in summary:
        parts.append("- Stale deployment telemetry")
    if any(k in summary for k in ("workflow", "github", "rerun")):
        parts.append("- Failed workflow reruns")
    if "railway" in summary or "verification" in summary:
        parts.append("- Railway verification gaps")
    if event.get("fatigue_decay"):
        parts.append("- Priority decayed due to prior operator dismissal")
    return "\n".join(parts)
