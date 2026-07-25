# SPDX-License-Identifier: Apache-2.0
"""Stabilization windows — delayed recovery verification."""

from __future__ import annotations

from typing import Any


def define_stabilization_windows() -> dict[str, Any]:
    return {
        "windows": [
            {"name": "immediate", "delay_minutes": 0},
            {"name": "short_tail", "delay_minutes": 15},
            {"name": "long_tail", "delay_minutes": 60},
        ],
        "operational_patience": True,
        "summary": "Delayed recovery verification windows active.",
    }
