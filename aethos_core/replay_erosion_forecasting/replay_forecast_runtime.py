# SPDX-License-Identifier: Apache-2.0
"""Replay forecast runtime — replay orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_erosion_forecasting.erosion_prediction import predict_erosion
from aethos_core.replay_erosion_forecasting.replay_durability_decay import assess_replay_durability_decay
from aethos_core.replay_erosion_forecasting.replay_forecast_memory import record_replay_forecast_memory
from aethos_core.replay_erosion_forecasting.replay_forecast_storytelling import tell_replay_forecast_story
from aethos_core.replay_erosion_forecasting.replay_pressure_projection import project_replay_pressure


def orchestrate_replay_forecast() -> dict[str, Any]:
    erosion = predict_erosion()
    pressure = project_replay_pressure()
    decay = assess_replay_durability_decay()
    story = tell_replay_forecast_story(resilient=not erosion.get("escalation_risk", False))
    memory = record_replay_forecast_memory(stable=pressure.get("pressure_stable", False))
    return {
        "erosion_prediction": erosion,
        "pressure_projection": pressure,
        "durability_decay": decay,
        "story": story,
        "memory": memory,
        "summary": erosion.get("summary", "Replay erosion forecasting active."),
    }
