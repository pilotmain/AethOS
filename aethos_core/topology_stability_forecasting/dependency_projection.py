# SPDX-License-Identifier: Apache-2.0
"""Dependency projection — downstream collapse forecasting."""

from __future__ import annotations

from typing import Any

from aethos_core.recovery_convergence.dependency_recovery_tracking import track_dependency_recovery


def project_dependency_collapse() -> dict[str, Any]:
    dep = track_dependency_recovery()
    collapse_risk = not dep.get("downstream_stable", False)
    return {
        **dep,
        "collapse_risk": collapse_risk,
        "summary": "Downstream collapse risk low." if not collapse_risk else "Dependency collapse risk emerging.",
    }
