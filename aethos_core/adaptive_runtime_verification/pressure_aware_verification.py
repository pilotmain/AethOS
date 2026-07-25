# SPDX-License-Identifier: Apache-2.0
"""Pressure aware verification — operational pressure pacing."""

from __future__ import annotations

from typing import Any

from aethos_core.adaptive_sustained_verification.operational_pressure_windows import assess_operational_pressure_windows


def run_pressure_aware_verification() -> dict[str, Any]:
    pressure = assess_operational_pressure_windows()
    return {
        **pressure,
        "summary": "Pressure-aware verification pacing active across operational windows.",
    }
