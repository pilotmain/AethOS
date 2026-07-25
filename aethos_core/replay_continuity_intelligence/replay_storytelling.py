# SPDX-License-Identifier: Apache-2.0
"""Replay storytelling — operational narratives."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_truth_convergence.replay_truth_alignment import align_replay_truth


def build_replay_story() -> dict[str, Any]:
    replay = align_replay_truth()
    return {
        **replay,
        "narrative": (
            "Replay continuity remains operationally stable across sustained runtime windows, "
            "with no significant degradation trajectories currently emerging."
        )
        if replay.get("replay_converged")
        else "Replay continuity evolution under extended reconciliation.",
    }
