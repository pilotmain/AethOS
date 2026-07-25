# SPDX-License-Identifier: Apache-2.0
"""Recovery convergence aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.recovery_convergence.convergence_confidence import assess_convergence_confidence
from aethos_core.recovery_convergence.dependency_recovery_tracking import track_dependency_recovery
from aethos_core.recovery_convergence.recovery_convergence_runtime import orchestrate_recovery_convergence
from aethos_core.recovery_convergence.recovery_decay_detection import detect_recovery_decay
from aethos_core.recovery_convergence.replay_recovery_convergence import converge_replay_recovery
from aethos_core.recovery_convergence.topology_recovery_tracking import track_topology_recovery


def assess_recovery_convergence(*, provider: str = "railway") -> dict[str, Any]:
    recovery = orchestrate_recovery_convergence(provider=provider)
    dependency = track_dependency_recovery()
    replay = converge_replay_recovery()
    topology = track_topology_recovery()
    decay = detect_recovery_decay()
    confidence = assess_convergence_confidence()
    continuous = recovery.get("converged") and dependency.get("downstream_stable")
    return {
        "ok": True,
        "recovery": recovery,
        "dependency_tracking": dependency,
        "replay_convergence": replay,
        "topology_tracking": topology,
        "recovery_decay": decay,
        "convergence_confidence": confidence,
        "continuously_reconciled": continuous,
        "summary": "Recovery continuously reconciled across dependent runtime surfaces."
        if continuous
        else "Recovery convergence monitoring active — systems remain under sustained observation.",
    }
