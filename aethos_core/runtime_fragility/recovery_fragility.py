# SPDX-License-Identifier: Apache-2.0
"""Recovery fragility — unstable recovery pathways."""

from __future__ import annotations

from typing import Any

from aethos_core.infrastructure_fragility.recovery_asymmetry import detect_recovery_asymmetry
from aethos_core.long_tail_stability.recovery_fragility import detect_recovery_fragility as detect_weak_recovery


def assess_recovery_fragility() -> dict[str, Any]:
    asymmetry = detect_recovery_asymmetry()
    fragility = detect_weak_recovery()
    unstable = asymmetry.get("asymmetric") or fragility.get("fragile", False)
    return {
        "asymmetry": asymmetry,
        "weak_recovery": fragility,
        "unstable": unstable,
        "summary": "Unstable recovery pathways detected." if unstable else "Recovery pathways remain durable under stress.",
    }
