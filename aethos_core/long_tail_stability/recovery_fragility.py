# SPDX-License-Identifier: Apache-2.0
"""Recovery fragility — weak recovery detection."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_operational_decay.stabilization_regression import assess_stabilization_regression


def detect_recovery_fragility(*, stable: bool = True) -> dict[str, Any]:
    regression = assess_stabilization_regression(stable=stable)
    fragile = regression.get("regression_detected", False)
    return {
        **regression,
        "fragile": fragile,
        "summary": "Recovery fragility detected." if fragile else "No significant recovery fragility currently detected.",
    }
