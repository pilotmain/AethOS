# SPDX-License-Identifier: Apache-2.0
"""Replay runtime — replay orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_erosion_intelligence.erosion_prediction import predict_replay_erosion
from aethos_core.replay_erosion_intelligence.replay_memory import record_replay_erosion_memory
from aethos_core.replay_erosion_intelligence.replay_pressure_analysis import analyze_replay_pressure
from aethos_core.replay_erosion_intelligence.replay_resilience_decay import assess_replay_resilience_decay
from aethos_core.replay_erosion_intelligence.replay_story_evolution import evolve_replay_story


def orchestrate_replay_erosion() -> dict[str, Any]:
    erosion = predict_replay_erosion()
    pressure = analyze_replay_pressure()
    decay = assess_replay_resilience_decay()
    story = evolve_replay_story(resilient=not erosion.get("escalation_risk", False))
    memory = record_replay_erosion_memory(stable=pressure.get("pressure_stable", False))
    return {
        "erosion_prediction": erosion,
        "pressure_analysis": pressure,
        "resilience_decay": decay,
        "story": story,
        "memory": memory,
        "summary": erosion.get("summary", "Replay erosion intelligence active."),
    }
