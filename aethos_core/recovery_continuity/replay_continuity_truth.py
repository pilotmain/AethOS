# SPDX-License-Identifier: Apache-2.0
"""Replay continuity truth — replay persistence."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_truth_convergence.replay_truth_alignment import align_replay_truth


def assess_replay_continuity_truth() -> dict[str, Any]:
    replay = align_replay_truth()
    return {
        **replay,
        "persistence_stable": replay.get("replay_converged", False),
        "summary": "Replay continuity remains stable across sustained operational windows." if replay.get("replay_converged") else "Replay continuity truth monitoring active.",
    }
