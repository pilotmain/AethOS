# SPDX-License-Identifier: Apache-2.0
"""Contextual operational reasoning — intent-aware signal routing."""

from __future__ import annotations

import re
from typing import Any

_INTENT_RX = {
    "deployment": re.compile(r"\b(deployment|railway|vercel|restart|rollout|deploy)\b", re.I),
    "engineering": re.compile(r"\b(engineering|preflight|patch|validation|pytest|sandbox)\b", re.I),
    "browser": re.compile(r"\b(browser|dns|ui|screenshot|runtime evidence)\b", re.I),
    "dependency": re.compile(r"\b(dependency|cve|npm|modernization|package)\b", re.I),
    "workflow": re.compile(r"\b(workflow|github|ci|rerun|actions)\b", re.I),
}

_SOURCE_WEIGHTS: dict[str, dict[str, float]] = {
    "deployment": {
        "deployment_instability": 1.0,
        "flaky_workflow": 0.85,
        "operational_intelligence": 0.8,
        "railway": 1.0,
        "recommendation": 0.7,
        "repo_drift_scan": 0.05,
        "internal_substrate": 0.02,
    },
    "engineering": {
        "engineering": 1.0,
        "workspace": 0.9,
        "validation": 0.85,
        "deployment_instability": 0.4,
        "internal_substrate": 0.1,
    },
    "dependency": {
        "dependency_churn": 1.0,
        "dependency": 1.0,
        "operational_intelligence": 0.6,
        "internal_substrate": 0.05,
    },
    "operational": {
        "operational_intelligence": 1.0,
        "recommendation": 0.9,
        "deployment_instability": 0.8,
        "flaky_workflow": 0.8,
    },
}

_INTERNAL_NOISE = frozenset({"repo_drift_scan", "recommendation_generated", "presence_cycle"})


def infer_operational_intent(user_text: str | None = None, *, focus: dict[str, Any] | None = None) -> str:
    if focus and focus.get("mode") == "deployment_debug":
        return "deployment"
    if focus and focus.get("mode") == "dependency_review":
        return "dependency"
    text = user_text or ""
    for intent, rx in _INTENT_RX.items():
        if rx.search(text):
            return intent
    if _INTENT_RX["deployment"].search(text):
        return "deployment"
    return "operational"


def route_signals_by_context(
    events: list[dict[str, Any]],
    *,
    intent: str = "operational",
    focus: dict[str, Any] | None = None,
    hide_internal_unless_critical: bool = True,
) -> list[dict[str, Any]]:
    """Filter and weight signals for contextual relevance."""
    focus_mode = (focus or {}).get("mode")
    if focus_mode == "deployment_debug":
        intent = "deployment"
    weights = _SOURCE_WEIGHTS.get(intent, _SOURCE_WEIGHTS["operational"])
    routed: list[dict[str, Any]] = []

    for event in events:
        source = str(event.get("source") or "")
        summary = str(event.get("summary") or "").lower()
        signal_class = str(event.get("signal_class") or "")

        if _is_internal_noise(source, summary, signal_class):
            if hide_internal_unless_critical and intent != "engineering":
                weight = weights.get("internal_substrate", 0.02)
                if weight < 0.1:
                    continue
            event = {**event, "signal_class": "internal_substrate"}

        weight = _weight_for_event(event, weights)
        if focus_mode == "deployment_debug" and weight < 0.15 and str(event.get("priority", "")).lower() not in ("critical",):
            continue
        if focus_mode == "dependency_review" and "dependency" not in source and "dependency" not in summary and weight < 0.2:
            continue

        routed.append({**event, "context_weight": round(weight, 2), "routing_intent": intent})

    routed.sort(key=lambda e: (e.get("context_weight", 0), e.get("attention_score", 0)), reverse=True)
    return routed


def _is_internal_noise(source: str, summary: str, signal_class: str) -> bool:
    if signal_class == "internal_substrate":
        return True
    if "repo_drift" in summary or "repo drift" in summary:
        return True
    if any(tok in summary for tok in _INTERNAL_NOISE):
        return True
    if source in ("repo_drift_scan", "presence_cycle"):
        return True
    return False


def _weight_for_event(event: dict[str, Any], weights: dict[str, float]) -> float:
    source = str(event.get("source") or "")
    summary = str(event.get("summary") or "").lower()
    best = 0.2
    for key, w in weights.items():
        if key in source or key.replace("_", " ") in summary or key in summary:
            best = max(best, w)
    if "railway" in summary or "deployment" in summary:
        best = max(best, weights.get("deployment_instability", 0.5))
    if "workflow" in summary or "github" in summary:
        best = max(best, weights.get("flaky_workflow", 0.5))
    return best
