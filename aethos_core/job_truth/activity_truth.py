# SPDX-License-Identifier: Apache-2.0
"""Last-activity integrity — Phase 11.8.0."""

from __future__ import annotations

from time import time
from typing import Any


def _ts(job: dict[str, Any], key: str) -> float | None:
    value = job.get(key)
    return float(value) if value else None


def last_activity_timestamp(job: dict[str, Any]) -> float | None:
    """Most recent meaningful activity timestamp for a job."""
    status = str(job.get("status") or "")
    if status in {"completed", "failed", "cancelled"}:
        candidates = [_ts(job, "updated_at"), _ts(job, "completed_at"), _ts(job, "started_at")]
    else:
        candidates = [_ts(job, "updated_at"), _ts(job, "completed_at"), _ts(job, "started_at"), _ts(job, "created_at")]
    present = [c for c in candidates if c is not None]
    return max(present) if present else None


def format_last_activity(*, seconds_ago: float) -> str:
    if seconds_ago < 60:
        return "just now"
    if seconds_ago < 3600:
        minutes = int(seconds_ago // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    if seconds_ago < 86400:
        hours = int(seconds_ago // 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = int(seconds_ago // 86400)
    return f"{days} day{'s' if days != 1 else ''} ago"


def describe_last_activity(job: dict[str, Any], *, now: float | None = None) -> dict[str, Any]:
    now_ts = now if now is not None else time()
    last = last_activity_timestamp(job)
    if last is None:
        return {"last_activity_at": None, "last_activity_phrase": "no recorded activity", "seconds_ago": None}
    seconds_ago = max(0.0, now_ts - last)
    return {
        "last_activity_at": last,
        "seconds_ago": round(seconds_ago, 1),
        "last_activity_phrase": format_last_activity(seconds_ago=seconds_ago),
    }
