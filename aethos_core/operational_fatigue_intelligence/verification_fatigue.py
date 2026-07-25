# SPDX-License-Identifier: Apache-2.0
"""Verification fatigue — verification exhaustion."""

from __future__ import annotations

from typing import Any

from aethos_core.adaptive_sustained_verification.verification_decay_tracking import track_verification_decay


def assess_verification_fatigue() -> dict[str, Any]:
    decay = track_verification_decay()
    exhausted = not decay.get("erosion_bounded", True)
    return {
        **decay,
        "exhausted": exhausted,
        "summary": "Verification fatigue within acceptable bounds." if not exhausted else "Verification exhaustion emerging.",
    }
