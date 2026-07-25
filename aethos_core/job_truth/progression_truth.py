# SPDX-License-Identifier: Apache-2.0
"""Progression certainty bounds — Phase 11.8.0."""

from __future__ import annotations

from typing import Any


def bound_progression_confidence(
    *,
    has_active_jobs: bool,
    has_completed_jobs: bool,
    freshness_tier: str,
    stalled_count: int = 0,
) -> dict[str, Any]:
    if stalled_count > 0:
        return {
            "confidence": 0.45,
            "certainty_tier": "low",
            "phrase": "Progression confidence is reduced while stalled jobs remain unresolved.",
        }
    if has_active_jobs and freshness_tier == "fresh":
        return {
            "confidence": 0.72,
            "certainty_tier": "moderate",
            "phrase": "Progression is backed by active durable jobs with recent activity.",
        }
    if has_completed_jobs and not has_active_jobs:
        if freshness_tier == "stale":
            return {
                "confidence": 0.55,
                "certainty_tier": "moderate-low",
                "phrase": "Latest completed passes are recorded, but continuity is decay-aware due to age.",
            }
        return {
            "confidence": 0.78,
            "certainty_tier": "moderate-high",
            "phrase": "Latest completed passes are artifact-backed; no jobs are currently running.",
        }
    return {
        "confidence": 0.5,
        "certainty_tier": "moderate-low",
        "phrase": "Progression confidence is bounded — ask for a specific agent or job update.",
    }
