# SPDX-License-Identifier: Apache-2.0
"""Stability windows — sustained runtime windows."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_verification_windows.verification_windows import assess_verification_windows


def assess_stability_windows(*, hours_elapsed: float = 5.0) -> dict[str, Any]:
    windows = assess_verification_windows(hours_elapsed=hours_elapsed)
    return {
        **windows,
        "summary": (
            "Operational stability remained healthy through the sustained runtime verification window, "
            "with no significant dependency degradation detected."
        )
        if windows.get("window_satisfied")
        else "Sustained runtime verification window active.",
    }
