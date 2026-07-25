# SPDX-License-Identifier: Apache-2.0
"""Dependency resilience — downstream resilience."""

from __future__ import annotations

from typing import Any

from aethos_core.recovery_convergence.dependency_recovery_tracking import track_dependency_recovery


def assess_dependency_resilience() -> dict[str, Any]:
    dep = track_dependency_recovery()
    resilient = dep.get("downstream_stable", False)
    return {
        **dep,
        "resilient": resilient,
        "summary": "Downstream dependency resilience maintained." if resilient else "Dependency resilience monitoring active.",
    }
