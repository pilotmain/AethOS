# SPDX-License-Identifier: Apache-2.0
"""Freshness-aware operational language — Phase 11.8.0."""

from __future__ import annotations

from time import time
from typing import Any

STALE_CONTINUITY_SECONDS = 86400  # 24h
AGING_CONTINUITY_SECONDS = 3600  # 1h


def freshness_tier(*, seconds_since_activity: float | None) -> str:
    if seconds_since_activity is None:
        return "unknown"
    if seconds_since_activity >= STALE_CONTINUITY_SECONDS:
        return "stale"
    if seconds_since_activity >= AGING_CONTINUITY_SECONDS:
        return "aging"
    return "fresh"


def freshness_phrase(tier: str) -> str:
    if tier == "stale":
        return "last known activity is more than 24 hours old — continuity is decay-aware, not actively running"
    if tier == "aging":
        return "last meaningful activity was over an hour ago — awaiting the next scheduled check or follow-up"
    if tier == "fresh":
        return "recent activity is within the current operational window"
    return "activity freshness is unknown — confidence is bounded"


def assess_freshness(*, seconds_since_activity: float | None) -> dict[str, Any]:
    tier = freshness_tier(seconds_since_activity=seconds_since_activity)
    return {
        "freshness_tier": tier,
        "freshness_phrase": freshness_phrase(tier),
        "stale_context": tier == "stale",
        "requires_decay_language": tier in {"stale", "aging"},
    }


def session_freshness(*, jobs: list[dict[str, Any]], now: float | None = None) -> dict[str, Any]:
    from aethos_core.job_truth.activity_truth import last_activity_timestamp

    now_ts = now if now is not None else time()
    if not jobs:
        return assess_freshness(seconds_since_activity=None)
    last = max(filter(None, (last_activity_timestamp(j) for j in jobs)), default=None)
    seconds = (now_ts - last) if last is not None else None
    return assess_freshness(seconds_since_activity=seconds)
