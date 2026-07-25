# SPDX-License-Identifier: Apache-2.0
"""Sustained health — long-tail operational trust."""

from __future__ import annotations

from typing import Any


def assess_sustained_health(*, hours_stable: float = 2.0, threshold_hours: float = 4.0) -> dict[str, Any]:
    qualified = hours_stable >= threshold_hours
    return {
        "hours_stable": hours_stable,
        "threshold_hours": threshold_hours,
        "sustained_health_qualified": qualified,
        "summary": "Long-tail operational stability converging."
        if not qualified
        else "Sustained health qualified across extended monitoring window.",
    }
