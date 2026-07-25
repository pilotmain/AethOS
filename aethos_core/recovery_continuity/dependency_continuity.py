# SPDX-License-Identifier: Apache-2.0
"""Dependency continuity — downstream recovery continuity."""

from __future__ import annotations

from typing import Any

from aethos_core.recovery_convergence.dependency_recovery_tracking import track_dependency_recovery


def assess_dependency_continuity() -> dict[str, Any]:
    dep = track_dependency_recovery()
    return {
        **dep,
        "continuity_held": dep.get("downstream_stable", False),
        "summary": "Dependency recovery continuity held across sustained windows." if dep.get("downstream_stable") else "Dependency continuity monitoring active.",
    }
