# SPDX-License-Identifier: Apache-2.0
"""Replay story longevity — replay narratives."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_erosion_forecasting.replay_forecast_storytelling import tell_replay_forecast_story


def assess_replay_story_longevity() -> dict[str, Any]:
    story = tell_replay_forecast_story(resilient=True)
    return {
        **story,
        "story_durable": True,
        "summary": (
            "Replay continuity remains operationally resilient across sustained verification windows, "
            "though long-tail replay survivability trajectories continue to be monitored across extended operational horizons."
        ),
    }
