# SPDX-License-Identifier: Apache-2.0
"""Replay fatigue — replay strain accumulation."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_resilience.replay_pressure_tracking import track_replay_stress


def assess_replay_fatigue() -> dict[str, Any]:
    replay = track_replay_stress()
    strained = not replay.get("pressure_stable", True)
    return {
        **replay,
        "strained": strained,
        "summary": "Replay strain accumulation within bounds." if not strained else "Replay stress accumulation emerging.",
    }
