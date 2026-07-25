# SPDX-License-Identifier: Apache-2.0
"""Realism scoring — Phase 11.8.2."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.live_operational_grounding.regression_guardrails import assess_regression_guardrails

_BAD_CERTAINTY = (
    "everything is healthy",
    "everything looks healthy",
    "fully resolved",
    "completely healthy",
    "analysis completed successfully",
    "the analysis completed",
    "deployment stabilized successfully",
)
_BAD_SPAM = (r"\bretrying\.{0,3}\b", r"\bretrying\b.*\bretrying\b")
_GOOD_BOUNDED = (
    "verification window",
    "extended monitoring",
    "progression confidence",
    "last activity",
    "callback",
    "awaiting",
    "bounded",
    "moderate",
    "decay",
    "stale",
    "retry",
    "transient",
)


def score_turn(
    *,
    reply: str,
    scenario_id: str,
    user_text: str = "",
    guardrails: dict[str, Any] | None = None,
) -> dict[str, Any]:
    lower = reply.lower()
    guard = guardrails or assess_regression_guardrails(reply=reply, grounded=True)
    violations = list(guard.get("violations") or [])

    hallucination_risk = "low"
    if any(p in lower for p in _BAD_CERTAINTY):
        hallucination_risk = "high"
        violations.append("overconfident_certainty")
    elif "don't have visibility" in lower or "generic" in lower:
        hallucination_risk = "medium"

    notification_quality = "calm"
    if len(re.findall(r"\bretrying\b", lower)) >= 3:
        notification_quality = "noisy"
        violations.append("retry_spam")

    freshness_integrity = "bounded"
    if any(w in lower for w in ("24 hours", "decay", "stale", "older rather than moments ago")):
        freshness_integrity = "stale-aware"
    if any(p in lower for p in _BAD_CERTAINTY):
        freshness_integrity = "broken"

    ambiguity_handling = "safe"
    if scenario_id == "parallel_investigation_drift":
        if "replay" in (user_text or "").lower() and "railway" in lower and "replay" not in lower:
            ambiguity_handling = "unsafe"
            violations.append("subject_conflation")
        elif "replay" in lower and ("moderate" in lower or "multiple" in lower or "thread" in lower):
            ambiguity_handling = "safe"

    retry_behavior = "healthy"
    if "retry" in lower and notification_quality == "noisy":
        retry_behavior = "fatiguing"
    elif "transient" in lower and "retry" in lower:
        retry_behavior = "healthy"

    emotional_stability = "calm"
    if any(w in lower for w in ("urgent", "critical failure", "immediately failed", "panic")):
        emotional_stability = "volatile"

    continuity_quality = "preserved" if guard.get("guardrails_qualified") else "degraded"
    truth_alignment = "runtime agreement" if guard.get("guardrails_qualified") else "partial agreement"
    operational_realism = "believable" if len(violations) <= 1 else "synthetic"

    good_hits = sum(1 for g in _GOOD_BOUNDED if g in lower)
    realism_score = max(0.0, min(1.0, 0.55 + good_hits * 0.07 - len(violations) * 0.12))

    return {
        "continuity_quality": continuity_quality,
        "truth_alignment": truth_alignment,
        "hallucination_risk": hallucination_risk,
        "freshness_integrity": freshness_integrity,
        "notification_quality": notification_quality,
        "operational_realism": operational_realism,
        "retry_behavior": retry_behavior,
        "ambiguity_handling": ambiguity_handling,
        "emotional_stability": emotional_stability,
        "operational_realism_score": realism_score,
        "guardrails_qualified": guard.get("guardrails_qualified", False),
        "violations": violations,
    }
