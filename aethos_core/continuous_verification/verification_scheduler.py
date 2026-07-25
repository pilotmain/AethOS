# SPDX-License-Identifier: Apache-2.0
"""Verification scheduler — recurring verification windows."""

from __future__ import annotations

from typing import Any


def schedule_verification_windows(*, extended: bool = True) -> dict[str, Any]:
    windows = [
        {"phase": "immediate", "duration_minutes": 5, "active": True},
        {"phase": "stabilization", "duration_minutes": 30, "active": extended},
        {"phase": "long_tail", "duration_minutes": 120, "active": extended},
    ]
    return {
        "windows": windows,
        "active_count": sum(1 for w in windows if w["active"]),
        "summary": f"{sum(1 for w in windows if w['active'])} verification windows scheduled.",
    }
