# SPDX-License-Identifier: Apache-2.0
"""Verification decay — confidence erosion over time."""

from __future__ import annotations

from typing import Any


def assess_verification_decay(*, base: float = 0.85, hours: float = 3.0) -> dict[str, Any]:
    current = max(0.4, base - 0.015 * hours)
    return {
        "base_confidence": base,
        "current_confidence": round(current, 2),
        "erosion_bounded": current >= 0.65,
        "summary": "Verification confidence erosion bounded." if current >= 0.65 else "Verification confidence erosion detected.",
    }
