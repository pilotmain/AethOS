# SPDX-License-Identifier: Apache-2.0
"""Recovery asymmetry — uneven stabilization."""

from __future__ import annotations

from typing import Any

from aethos_core.recovery_convergence.dependency_recovery_tracking import track_dependency_recovery
from aethos_core.recovery_convergence.topology_recovery_tracking import track_topology_recovery


def detect_recovery_asymmetry() -> dict[str, Any]:
    dep = track_dependency_recovery()
    topo = track_topology_recovery()
    asymmetric = dep.get("downstream_stable") != topo.get("topology_converged")
    return {
        "dependency_stable": dep.get("downstream_stable", False),
        "topology_converged": topo.get("topology_converged", False),
        "asymmetric": asymmetric,
        "summary": "Recovery asymmetry detected across dependency surfaces." if asymmetric else "Recovery stabilization symmetric across surfaces.",
    }
