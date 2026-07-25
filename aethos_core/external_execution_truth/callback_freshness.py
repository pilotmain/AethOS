# SPDX-License-Identifier: Apache-2.0
"""Webhook callback freshness tiers — Phase 11.8.1."""

from __future__ import annotations

from time import time
from typing import Any

CALLBACK_FRESHNESS_TIERS = ("fresh", "aging", "stale", "missing", "contradictory")


def assess_callback_freshness(
    *,
    dispatched_at: float | None,
    last_callback_at: float | None,
    stale_callback_minutes: int = 10,
    now: float | None = None,
) -> dict[str, Any]:
    now_ts = now if now is not None else time()
    if dispatched_at is None:
        return {"tier": "missing", "phrase": "no external dispatch recorded", "confidence_factor": 0.5}
    if last_callback_at is None:
        elapsed_min = (now_ts - dispatched_at) / 60.0
        if elapsed_min >= stale_callback_minutes:
            return {
                "tier": "missing",
                "phrase": "external execution has not produced a fresh callback within the expected verification window",
                "confidence_factor": 0.45,
                "elapsed_minutes": round(elapsed_min, 1),
            }
        return {
            "tier": "aging",
            "phrase": "awaiting external execution confirmation",
            "confidence_factor": 0.6,
            "elapsed_minutes": round(elapsed_min, 1),
        }
    elapsed_min = (now_ts - last_callback_at) / 60.0
    if elapsed_min >= stale_callback_minutes:
        return {
            "tier": "stale",
            "phrase": "callback freshness is degraded — progression confidence is limited until a newer signal arrives",
            "confidence_factor": 0.5,
            "elapsed_minutes": round(elapsed_min, 1),
        }
    if elapsed_min >= stale_callback_minutes / 2:
        return {
            "tier": "aging",
            "phrase": "callback is delayed but still within a plausible verification window",
            "confidence_factor": 0.65,
            "elapsed_minutes": round(elapsed_min, 1),
        }
    return {
        "tier": "fresh",
        "phrase": "external execution callback is recent",
        "confidence_factor": 0.85,
        "elapsed_minutes": round(elapsed_min, 1),
    }
