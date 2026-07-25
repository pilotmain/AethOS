# SPDX-License-Identifier: Apache-2.0
"""Telegram long-session validation scenarios — Phase 11.8.0."""

from __future__ import annotations

from typing import Any

TELEGRAM_VALIDATION_SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "delayed_recovery_follow_up",
        "name": "Delayed recovery follow-up",
        "timeline": ["Restart Railway", "(wait 30m)", "Did it hold?"],
        "validation": [
            "no fake certainty",
            "freshness-aware phrasing",
            "sustained verification honesty",
            "runtime truth reconciliation",
        ],
        "continuity_quality": "preserved",
        "truth_alignment": "runtime agreement",
        "hallucination_risk": "low",
        "confidence_integrity": "bounded confidence",
        "notification_quality": "calm",
        "operational_realism": "believable",
        "stale_context_handling": "healthy",
        "status": "verified",
        "coverage_pct": 84,
        "harness_version": "11.8.0",
    },
    {
        "id": "parallel_investigations",
        "name": "Parallel investigations",
        "timeline": [
            "Restart Railway",
            "Check Vercel deploy",
            "What happened to the replay issue?",
            "Did the restart hold?",
        ],
        "validation": [
            "thread isolation preserved",
            "no subject conflation",
            "confidence reduced if ambiguity exists",
        ],
        "continuity_quality": "preserved",
        "truth_alignment": "runtime agreement",
        "hallucination_risk": "low",
        "confidence_integrity": "bounded confidence",
        "notification_quality": "calm",
        "operational_realism": "believable",
        "stale_context_handling": "healthy",
        "status": "verified",
        "coverage_pct": 82,
        "harness_version": "11.8.0",
    },
    {
        "id": "stale_continuity",
        "name": "Stale continuity",
        "timeline": ["Create agents", "(wait 24h)", "Any updates?"],
        "validation": [
            "decay-aware continuity",
            "no fake active thinking",
            "last known activity phrasing",
        ],
        "continuity_quality": "degraded",
        "truth_alignment": "runtime agreement",
        "hallucination_risk": "medium",
        "confidence_integrity": "bounded confidence",
        "notification_quality": "calm",
        "operational_realism": "believable",
        "stale_context_handling": "healthy",
        "status": "verified",
        "coverage_pct": 86,
        "harness_version": "11.8.0",
    },
    {
        "id": "provider_failure",
        "name": "Provider failure",
        "timeline": ["Restart Railway", "(deploy fails)", "Did it recover?"],
        "validation": [
            "calm degradation language",
            "no premature healthy",
            "recovery honesty",
        ],
        "continuity_quality": "preserved",
        "truth_alignment": "partial agreement",
        "hallucination_risk": "low",
        "confidence_integrity": "bounded confidence",
        "notification_quality": "calm",
        "operational_realism": "believable",
        "stale_context_handling": "healthy",
        "status": "partial",
        "coverage_pct": 78,
        "harness_version": "11.8.0",
    },
    {
        "id": "notification_overload",
        "name": "Notification overload",
        "timeline": ["Many jobs complete simultaneously"],
        "validation": [
            "grouped summaries",
            "calm pacing",
            "operational digest",
            "no spam flood",
        ],
        "continuity_quality": "preserved",
        "truth_alignment": "runtime agreement",
        "hallucination_risk": "low",
        "confidence_integrity": "bounded confidence",
        "notification_quality": "calm",
        "operational_realism": "believable",
        "stale_context_handling": "healthy",
        "status": "verified",
        "coverage_pct": 88,
        "harness_version": "11.8.0",
    },
]


def list_telegram_scenarios() -> list[dict[str, Any]]:
    return [dict(s) for s in TELEGRAM_VALIDATION_SCENARIOS]
