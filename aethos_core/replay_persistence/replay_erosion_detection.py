# SPDX-License-Identifier: Apache-2.0
"""Replay erosion detection — replay degradation."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_operational_decay.replay_decay_tracking import track_replay_decay


def detect_replay_erosion() -> dict[str, Any]:
    decay = track_replay_decay()
    bounded = decay.get("erosion_bounded", True)
    return {
        **decay,
        "erosion_detected": not bounded,
        "summary": "No significant replay degradation trajectories currently emerging." if bounded else "Replay erosion detected — persistence monitoring active.",
    }
