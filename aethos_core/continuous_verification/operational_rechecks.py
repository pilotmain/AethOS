# SPDX-License-Identifier: Apache-2.0
"""Operational rechecks — scheduled operational truth checks."""

from __future__ import annotations

from typing import Any


def plan_operational_rechecks(*, windows: dict[str, Any]) -> dict[str, Any]:
    active = windows.get("active_count", 0)
    rechecks = [
        {"check": "runtime health", "interval_minutes": 15},
        {"check": "topology stability", "interval_minutes": 30},
        {"check": "telemetry consistency", "interval_minutes": 20},
        {"check": "degradation patterns", "interval_minutes": 45},
    ]
    return {
        "rechecks": rechecks[:active + 1],
        "scheduled_count": min(len(rechecks), active + 2),
        "summary": f"{min(len(rechecks), active + 2)} operational rechecks scheduled.",
    }
