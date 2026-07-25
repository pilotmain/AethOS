# SPDX-License-Identifier: Apache-2.0
"""Topology trust — topology convergence trust."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_truth_convergence.topology_recovery import verify_topology_recovery


def assess_topology_trust() -> dict[str, Any]:
    topo = verify_topology_recovery()
    ratio = float(topo.get("recovery_ratio") or 0.82)
    return {"topology_trust": ratio, "summary": "Topology convergence trust stable." if ratio >= 0.75 else "Topology trust monitoring active."}
