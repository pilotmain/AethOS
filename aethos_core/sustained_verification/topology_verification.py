# SPDX-License-Identifier: Apache-2.0
"""Topology verification — dependency convergence."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_truth_convergence.topology_recovery import verify_topology_recovery


def verify_topology_convergence() -> dict[str, Any]:
    recovery = verify_topology_recovery()
    return {
        **recovery,
        "topology_verified": recovery.get("topology_converged", False),
        "summary": "Dependency topology convergence verified." if recovery.get("topology_converged") else "Dependency topology convergence monitoring active.",
    }
