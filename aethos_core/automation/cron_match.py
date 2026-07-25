# SPDX-License-Identifier: Apache-2.0
"""Minimal five-field cron matcher (minute hour dom month dow, UTC)."""

from __future__ import annotations

from datetime import datetime, timezone


def _parse_field(field: str, value: int, min_v: int, max_v: int) -> bool:
    text = (field or "*").strip().lower()
    if text == "*":
        return True
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        step = 1
        if "/" in part:
            base, step_text = part.split("/", 1)
            step = max(1, int(step_text))
        else:
            base = part
        if base == "*":
            if (value - min_v) % step == 0:
                return True
            continue
        if "-" in base:
            start_s, end_s = base.split("-", 1)
            start = int(start_s)
            end = int(end_s)
            if start <= value <= end and (value - start) % step == 0:
                return True
            continue
        if int(base) == value:
            return True
    return False


def cron_matches(expression: str, when: datetime | None = None) -> bool:
    """Return True when ``when`` (UTC) matches the cron expression."""
    dt = when or datetime.now(timezone.utc)
    parts = (expression or "").split()
    if len(parts) != 5:
        return False
    minute, hour, dom, month, dow = parts
    return (
        _parse_field(minute, dt.minute, 0, 59)
        and _parse_field(hour, dt.hour, 0, 23)
        and _parse_field(dom, dt.day, 1, 31)
        and _parse_field(month, dt.month, 1, 12)
        and _parse_field(dow, dt.weekday(), 0, 6)
    )
