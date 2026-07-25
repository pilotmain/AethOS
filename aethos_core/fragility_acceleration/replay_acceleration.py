# SPDX-License-Identifier: Apache-2.0
"""Replay acceleration — replay degradation momentum."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_resilience.replay_erosion_prediction import forecast_replay_erosion


def detect_replay_acceleration() -> dict[str, Any]:
    erosion = forecast_replay_erosion()
    accelerating = erosion.get("escalation_risk", False)
    return {
        **erosion,
        "accelerating": accelerating,
        "summary": "Replay degradation momentum bounded." if not accelerating else "Replay degradation acceleration detected.",
    }
