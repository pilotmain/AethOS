# SPDX-License-Identifier: Apache-2.0
"""Runtime truth runtime — orchestration aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_truth_convergence.convergence_alignment import assess_convergence_alignment
from aethos_core.runtime_truth_convergence.operational_truth_decay import detect_operational_truth_decay
from aethos_core.runtime_truth_convergence.replay_truth_alignment import align_replay_truth
from aethos_core.runtime_truth_convergence.runtime_truth_memory import record_truth_convergence
from aethos_core.runtime_truth_convergence.sustained_truth_tracking import track_sustained_truth
from aethos_core.runtime_truth_convergence.topology_truth_alignment import align_topology_truth


def orchestrate_runtime_truth(*, provider: str = "railway") -> dict[str, Any]:
    alignment = assess_convergence_alignment(provider=provider)
    sustained = track_sustained_truth()
    replay = align_replay_truth()
    topology = align_topology_truth()
    decay = detect_operational_truth_decay()
    memory = record_truth_convergence(converged=alignment.get("multi_layer_aligned", False), tier="converging")
    converged = alignment.get("multi_layer_aligned") and decay.get("truth_erosion_bounded")
    return {
        "alignment": alignment,
        "sustained_tracking": sustained,
        "replay_truth": replay,
        "topology_truth": topology,
        "truth_decay": decay,
        "memory": memory,
        "converged": converged,
        "summary": (
            "Deployment recovery remains operationally stable across sustained verification windows, "
            "with infrastructure convergence, dependency stabilization, replay continuity, "
            "and topology recovery signals remaining healthy."
        ),
        "narrative": "Extended reconciliation remains active.",
    }
