# SPDX-License-Identifier: Apache-2.0
"""Attention engine — prioritize operational context."""

from __future__ import annotations

from time import time
from typing import Any


def score_attention(
    *,
    severity: str = "low",
    confidence: float = 0.5,
    recurrence: int = 0,
    freshness_hours: float | None = None,
    operational_impact: bool = False,
    focus_context: str | None = None,
) -> dict[str, Any]:
    score = 0.35
    score += {"low": 0.05, "medium": 0.15, "high": 0.28}.get(severity, 0.1)
    score += min(confidence * 0.25, 0.25)
    score += min(recurrence * 0.04, 0.2)
    if operational_impact:
        score += 0.12
    if freshness_hours is not None:
        if freshness_hours < 2:
            score += 0.1
        elif freshness_hours > 24:
            score -= 0.08
    if focus_context == "deployment_debug" and severity in ("high", "medium"):
        score += 0.08
    score = max(0.1, min(score, 0.98))
    priority = _priority_class(score, severity=severity)
    return {
        "attention_score": round(score, 2),
        "priority": priority,
        "attention_reason": _reason(severity, recurrence, operational_impact),
        "recommended_visibility": "show" if priority != "passive" else "feed_only",
    }


def rank_feed_events(events: list[dict[str, Any]], *, focus: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    focus_mode = (focus or {}).get("mode")
    ranked: list[dict[str, Any]] = []
    for event in events:
        att = score_attention(
            severity=str(event.get("severity") or "low"),
            confidence=float(event.get("confidence") or 0.6),
            recurrence=int(event.get("recurrence") or 0),
            freshness_hours=_age_hours(event.get("at")),
            operational_impact=bool(event.get("operational_impact")),
            focus_context=focus_mode,
        )
        ranked.append({**event, **att})
    ranked.sort(key=lambda e: e.get("attention_score", 0), reverse=True)
    return ranked


def _priority_class(score: float, *, severity: str) -> str:
    if severity == "high" and score >= 0.75:
        return "critical"
    if score >= 0.72:
        return "urgent"
    if score >= 0.5:
        return "elevated"
    return "passive"


def _reason(severity: str, recurrence: int, impact: bool) -> str:
    parts: list[str] = []
    if severity != "low":
        parts.append(f"{severity} severity")
    if recurrence >= 2:
        parts.append(f"recurring ({recurrence}x)")
    if impact:
        parts.append("operational impact")
    return "; ".join(parts) or "informational signal"


def _age_hours(at: float | None) -> float | None:
    if not at:
        return None
    return max(0.0, (time() - float(at)) / 3600.0)
