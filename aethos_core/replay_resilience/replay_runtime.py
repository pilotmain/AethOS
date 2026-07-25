# SPDX-License-Identifier: Apache-2.0
"""Replay runtime — replay orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_resilience.replay_erosion_prediction import forecast_replay_erosion
from aethos_core.replay_resilience.replay_memory import record_replay_memory
from aethos_core.replay_resilience.replay_pressure_tracking import track_replay_stress
from aethos_core.replay_resilience.replay_recovery_resilience import assess_replay_recovery_resilience
from aethos_core.replay_resilience.replay_story_resilience import build_replay_narrative


def orchestrate_replay_resilience() -> dict[str, Any]:
    pressure = track_replay_stress()
    erosion = forecast_replay_erosion()
    recovery = assess_replay_recovery_resilience()
    story = build_replay_narrative(resilient=not erosion.get("escalation_risk"))
    memory = record_replay_memory(stable=pressure.get("pressure_stable", False))
    resilient = pressure.get("pressure_stable") and not erosion.get("escalation_risk") and recovery.get("durable")
    return {
        "pressure_tracking": pressure,
        "erosion_prediction": erosion,
        "recovery_resilience": recovery,
        "story": story,
        "memory": memory,
        "resilient": resilient,
        "summary": story.get("narrative", "Replay resilience cognition active."),
    }
