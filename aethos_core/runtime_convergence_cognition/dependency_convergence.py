# SPDX-License-Identifier: Apache-2.0
"""Dependency convergence — downstream stabilization."""

from __future__ import annotations

from typing import Any

from aethos_core.recovery_convergence.dependency_recovery_tracking import track_dependency_recovery


def assess_dependency_convergence() -> dict[str, Any]:
    dep = track_dependency_recovery()
    return {
        **dep,
        "converged": dep.get("downstream_stable", False),
        "summary": "Dependency stabilization converging positively." if dep.get("downstream_stable") else "Dependency convergence monitoring active.",
    }
