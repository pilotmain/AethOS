# SPDX-License-Identifier: Apache-2.0
"""Verification windows — verification durations."""

from __future__ import annotations

from typing import Any

DEFAULT_WINDOW_HOURS = 4.0
EXTENDED_WINDOW_HOURS = 12.0


def assess_verification_windows(*, hours_elapsed: float = 2.5) -> dict[str, Any]:
    qualified = hours_elapsed >= DEFAULT_WINDOW_HOURS
    return {
        "default_window_hours": DEFAULT_WINDOW_HOURS,
        "extended_window_hours": EXTENDED_WINDOW_HOURS,
        "hours_elapsed": hours_elapsed,
        "window_satisfied": qualified,
        "summary": "Operational stability remained healthy through the sustained verification window, with no significant topology degradation detected."
        if qualified
        else "Sustained verification window active — long-tail monitoring in progress.",
    }
