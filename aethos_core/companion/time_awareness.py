# SPDX-License-Identifier: Apache-2.0
"""Time-aware supportive suggestions — optional, never blocking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


@dataclass
class TimeAwareSuggestion:
    kind: str
    message: str
    optional: bool = True
    blocking: bool = False


def current_local_hour(tz_name: str = "UTC") -> int:
    try:
        return datetime.now(ZoneInfo(tz_name)).hour
    except Exception:
        return datetime.utcnow().hour


def suggest_for_context(*, tz_name: str = "UTC") -> list[TimeAwareSuggestion]:
    suggestions: list[TimeAwareSuggestion] = []
    hour = current_local_hour(tz_name)
    if hour >= 23 or hour < 5:
        suggestions.append(
            TimeAwareSuggestion(
                kind="late_night",
                message=(
                    "It is getting late. You can continue if you want, but this may be a good stopping point. "
                    "I can package a handoff summary for tomorrow."
                ),
            )
        )
    return [s for s in suggestions if not s.blocking]


def suggestion_to_dict(s: TimeAwareSuggestion) -> dict[str, Any]:
    return {"kind": s.kind, "message": s.message, "optional": s.optional, "blocking": s.blocking}
