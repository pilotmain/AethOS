# SPDX-License-Identifier: Apache-2.0
"""Dependency trust — downstream stability trust."""

from __future__ import annotations

from typing import Any

from aethos_core.recovery_convergence.dependency_recovery_tracking import track_dependency_recovery


def assess_dependency_trust() -> dict[str, Any]:
    dep = track_dependency_recovery()
    stable = dep.get("downstream_stable", False)
    return {"dependency_trust": 0.85 if stable else 0.62, "summary": "Downstream stability trust held." if stable else "Dependency trust monitoring active."}
