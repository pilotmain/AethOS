# SPDX-License-Identifier: Apache-2.0
"""Replay resilience runtime — replay orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_resilience_intelligence.replay_erosion_prediction import predict_replay_erosion
from aethos_core.replay_resilience_intelligence.replay_pressure_tracking import track_replay_pressure
from aethos_core.replay_resilience_intelligence.replay_recovery_durability import assess_replay_recovery_durability
from aethos_core.replay_resilience_intelligence.replay_resilience_memory import record_replay_resilience_memory
from aethos_core.replay_resilience_intelligence.replay_story_resilience import build_replay_resilience_story


def orchestrate_replay_resilience() -> dict[str, Any]:
    pressure = track_replay_pressure()
    erosion = predict_replay_erosion()
    durability = assess_replay_recovery_durability()
    story = build_replay_resilience_story(resilient=not erosion.get("escalation_risk"))
    memory = record_replay_resilience_memory(stable=pressure.get("pressure_stable", False))
    resilient = pressure.get("pressure_stable") and not erosion.get("escalation_risk") and durability.get("durable")
    return {
        "pressure_tracking": pressure,
        "erosion_prediction": erosion,
        "recovery_durability": durability,
        "story": story,
        "memory": memory,
        "resilient": resilient,
        "summary": story.get("narrative", "Replay resilience intelligence active."),
    }
