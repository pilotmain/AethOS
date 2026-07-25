# SPDX-License-Identifier: Apache-2.0
"""Topology rollback truth — topology recovery verification."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_truth_convergence.topology_recovery import verify_topology_recovery


def assess_topology_rollback_truth() -> dict[str, Any]:
    recovery = verify_topology_recovery()
    return {
        **recovery,
        "rollback_topology_verified": recovery.get("topology_converged", False),
        "summary": "Topology rollback recovery verified." if recovery.get("topology_converged") else "Topology rollback recovery converging.",
    }
