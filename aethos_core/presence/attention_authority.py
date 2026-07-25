# SPDX-License-Identifier: Apache-2.0
"""Attention quality authority — disciplined priority classification."""

from __future__ import annotations

from time import time
from typing import Any

_PRIORITY_ORDER = {"PASSIVE": 0, "NOTICE": 1, "ELEVATED": 2, "URGENT": 3, "CRITICAL": 4}


def score_attention_quality(
    event: dict[str, Any],
    *,
    focus: dict[str, Any] | None = None,
    cluster: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute disciplined attention priority — avoid urgency inflation."""
    source = str(event.get("source") or "")
    summary = str(event.get("summary") or "").lower()
    signal_class = str(event.get("signal_class") or "")
    severity = str(event.get("severity") or "low")
    confidence = float(event.get("confidence") or 0.6)
    recurrence = int(event.get("recurrence") or event.get("dedupe_count") or 1)
    context_weight = float(event.get("context_weight") or 0.5)
    operational_impact = bool(event.get("operational_impact"))
    freshness = _freshness_hours(event)

    if signal_class == "internal_substrate" or "repo_drift" in summary:
        return _result(event, priority="PASSIVE", score=0.22, reason="Internal substrate scan — informational only.")

    if "stale_telemetry" in summary or source == "stale_telemetry":
        return _result(event, priority="NOTICE", score=0.35, reason="Stale telemetry — refresh diagnostics if needed.")

    score = 0.25
    score += context_weight * 0.25
    score += min(confidence * 0.2, 0.2)
    score += min((recurrence - 1) * 0.05, 0.15)

    if cluster and int(cluster.get("event_count") or 0) >= 2:
        score += 0.1

    if operational_impact:
        score += 0.08

    if freshness is not None and freshness < 2:
        score += 0.06

    focus_mode = (focus or {}).get("mode")
    if focus_mode == "deployment_debug" and _deployment_related(event):
        score += 0.1

    priority = _classify_priority(
        score=score,
        severity=severity,
        recurrence=recurrence,
        event=event,
        cluster=cluster,
    )
    reason = _build_reason(event, priority, recurrence, cluster)
    return _result(event, priority=priority, score=round(min(score, 0.95), 2), reason=reason)


def rank_with_attention_authority(
    events: list[dict[str, Any]],
    *,
    focus: dict[str, Any] | None = None,
    clusters: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    cluster_by_source = _cluster_lookup(clusters or [])
    ranked: list[dict[str, Any]] = []
    for event in events:
        key = str(event.get("source") or "")
        att = score_attention_quality(event, focus=focus, cluster=cluster_by_source.get(key))
        ranked.append({**event, **att})
    ranked.sort(key=lambda e: (_PRIORITY_ORDER.get(str(e.get("priority")), 0), e.get("attention_score", 0)), reverse=True)
    return ranked


def attention_quality_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for e in events:
        p = str(e.get("priority") or "PASSIVE")
        counts[p] = counts.get(p, 0) + 1
    inflation = counts.get("URGENT", 0) + counts.get("CRITICAL", 0)
    total = len(events) or 1
    return {
        "priority_distribution": counts,
        "urgency_inflation_ratio": round(inflation / total, 2),
        "high_signal_count": counts.get("ELEVATED", 0) + inflation,
        "passive_count": counts.get("PASSIVE", 0),
    }


def _classify_priority(
    *,
    score: float,
    severity: str,
    recurrence: int,
    event: dict[str, Any],
    cluster: dict[str, Any] | None,
) -> str:
    if _production_instability(event, cluster):
        return "CRITICAL" if recurrence >= 3 else "URGENT"

    if _deployment_related(event) and recurrence >= 2 and score >= 0.55:
        return "ELEVATED" if score < 0.72 else "URGENT"

    if severity == "high" and score >= 0.65 and recurrence >= 2:
        return "URGENT"

    if score >= 0.55 or severity == "medium":
        return "ELEVATED"

    if score >= 0.38:
        return "NOTICE"

    return "PASSIVE"


def _production_instability(event: dict[str, Any], cluster: dict[str, Any] | None) -> bool:
    summary = str(event.get("summary") or "").lower()
    if cluster and str(cluster.get("theme") or "") == "deployment_instability":
        return int(cluster.get("event_count") or 0) >= 3
    return "deployment_instability" in summary and int(event.get("recurrence") or 1) >= 3


def _deployment_related(event: dict[str, Any]) -> bool:
    s = str(event.get("summary") or "").lower()
    src = str(event.get("source") or "").lower()
    return any(k in s or k in src for k in ("deployment", "railway", "vercel", "restart", "workflow", "github"))


def _build_reason(event: dict[str, Any], priority: str, recurrence: int, cluster: dict[str, Any] | None) -> str:
    parts = [f"Priority {priority}"]
    if cluster:
        parts.append(f"cluster: {cluster.get('title', 'related signals')}")
    if recurrence > 1:
        parts.append(f"{recurrence} correlated signals")
    if event.get("provider"):
        parts.append(str(event["provider"]))
    return " · ".join(parts)


def _result(event: dict[str, Any], *, priority: str, score: float, reason: str) -> dict[str, Any]:
    return {
        "priority": priority,
        "attention_score": score,
        "attention_reason": reason,
        "recommended_visibility": "show" if priority not in ("PASSIVE",) else "feed_only",
    }


def _freshness_hours(event: dict[str, Any]) -> float | None:
    at = event.get("at") or event.get("created_at")
    if not at:
        return None
    return max(0.0, (time() - float(at)) / 3600.0)


def _cluster_lookup(clusters: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for c in clusters:
        for src in c.get("sources") or []:
            out[str(src)] = c
    return out
