# SPDX-License-Identifier: Apache-2.0
"""Recovery truth convergence aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.recovery_truth_convergence.confidence_recovery import assess_confidence_recovery
from aethos_core.recovery_truth_convergence.dependency_recovery_truth import assess_dependency_recovery_truth
from aethos_core.recovery_truth_convergence.recovery_decay import assess_recovery_decay
from aethos_core.recovery_truth_convergence.recovery_truth_runtime import orchestrate_recovery_truth
from aethos_core.recovery_truth_convergence.replay_recovery import assess_replay_recovery
from aethos_core.recovery_truth_convergence.topology_recovery_runtime import assess_topology_recovery_runtime


def assess_recovery_truth_convergence(*, provider: str = "railway") -> dict[str, Any]:
    recovery = orchestrate_recovery_truth(verification={"verified": False})
    dependency = assess_dependency_recovery_truth()
    replay = assess_replay_recovery()
    topology = assess_topology_recovery_runtime()
    decay = assess_recovery_decay(stable=True)
    confidence = assess_confidence_recovery()
    converged = dependency.get("downstream_stable") and topology.get("topology_converged")
    return {
        "ok": True,
        "provider": provider,
        "recovery": recovery,
        "dependency_recovery": dependency,
        "replay_recovery": replay,
        "topology_recovery": topology,
        "recovery_decay": decay,
        "confidence_recovery": confidence,
        "converged": converged,
        "summary": "Recovery truth converging across dependent runtime surfaces." if not converged else "Recovery truth converged.",
    }
