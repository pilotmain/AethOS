# SPDX-License-Identifier: Apache-2.0
"""Subject affinity — rank operational subjects against user prompt."""

from __future__ import annotations

import re
from typing import Any

_SUBJECT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "deployment": ("deployment", "deploy", "railway", "vercel", "release", "rollout"),
    "recovery": ("recovery", "recover", "restart", "rollback", "stabiliz", "hold"),
    "replay": ("replay", "continuity", "erosion", "session", "persistence"),
    "topology": ("topology", "dependency", "mesh", "cluster", "cascade", "downstream"),
    "provider": ("railway", "github", "vercel", "provider", "workflow", "ci"),
}


def _score_subject(text: str, keywords: tuple[str, ...]) -> float:
    lower = text.lower()
    return sum(1.0 for kw in keywords if kw in lower)


def rank_operational_subjects(
    *,
    user_text: str,
    bridge: dict[str, Any],
) -> list[dict[str, Any]]:
    """Rank candidate operational subjects by affinity to the current prompt."""
    candidates: list[dict[str, Any]] = []
    prompt_score = {k: _score_subject(user_text, kws) for k, kws in _SUBJECT_KEYWORDS.items()}

    def add(subject: str | None, category: str, *, recency_weight: float = 0.0) -> None:
        if not subject:
            return
        affinity = _score_subject(subject, _SUBJECT_KEYWORDS.get(category, ())) + prompt_score.get(category, 0.0)
        candidates.append({
            "subject": subject,
            "category": category,
            "affinity_score": round(affinity + recency_weight, 2),
        })

    add(bridge.get("deployment_subject"), "deployment", recency_weight=0.35)
    add(bridge.get("recovery_subject"), "recovery", recency_weight=0.25)
    add(bridge.get("replay_concern"), "replay", recency_weight=0.2)
    add(bridge.get("topology_concern"), "topology", recency_weight=0.2)
    add(bridge.get("primary_subject"), "recovery", recency_weight=0.15)
    for idx, inv in enumerate(bridge.get("active_investigations") or []):
        cat = _categorize(str(inv))
        add(str(inv), cat, recency_weight=max(0.1, 0.3 - idx * 0.05))
    for idx, topic in enumerate(bridge.get("focus_topics") or []):
        cat = _categorize(str(topic))
        add(str(topic), cat, recency_weight=max(0.05, 0.2 - idx * 0.04))

    seen: set[str] = set()
    ranked: list[dict[str, Any]] = []
    for item in sorted(candidates, key=lambda c: c["affinity_score"], reverse=True):
        key = item["subject"].lower()
        if key in seen:
            continue
        seen.add(key)
        ranked.append(item)
    return ranked[:5]


def select_primary_subject(
    *,
    user_text: str,
    bridge: dict[str, Any],
) -> dict[str, Any]:
    ranked = rank_operational_subjects(user_text=user_text, bridge=bridge)
    if not ranked:
        return {"subject": bridge.get("primary_subject"), "category": "general", "affinity_score": 0.0, "confident": False}
    top = ranked[0]
    second = ranked[1]["affinity_score"] if len(ranked) > 1 else 0.0
    margin = top["affinity_score"] - second
    confident = top["affinity_score"] >= 1.0 and margin >= 0.35
    return {**top, "confident": confident, "margin": round(margin, 2), "alternatives": ranked[1:3]}


def _categorize(text: str) -> str:
    lower = text.lower()
    for category, keywords in _SUBJECT_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return category
    return "recovery"
