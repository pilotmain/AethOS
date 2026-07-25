# SPDX-License-Identifier: Apache-2.0
"""Replay truth alignment — replay continuity."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_verification.replay_stability import assess_replay_stability


def align_replay_truth() -> dict[str, Any]:
    replay = assess_replay_stability()
    return {
        **replay,
        "replay_converged": replay.get("replay_stable", False),
        "summary": "Replay continuity converged across operational windows." if replay.get("replay_stable") else "Replay continuity convergence monitoring active.",
    }
