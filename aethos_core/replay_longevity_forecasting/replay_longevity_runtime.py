# SPDX-License-Identifier: Apache-2.0
"""Replay longevity runtime — orchestration aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_longevity_forecasting.continuity_longevity import assess_continuity_longevity
from aethos_core.replay_longevity_forecasting.replay_durability_projection import project_replay_durability_evolution
from aethos_core.replay_longevity_forecasting.replay_erosion_velocity import measure_replay_degradation_momentum
from aethos_core.replay_longevity_forecasting.replay_longevity_memory import record_replay_longevity_memory
from aethos_core.replay_longevity_forecasting.replay_story_longevity import assess_replay_story_longevity


def orchestrate_replay_longevity() -> dict[str, Any]:
    continuity = assess_continuity_longevity()
    durability = project_replay_durability_evolution()
    velocity = measure_replay_degradation_momentum()
    story = assess_replay_story_longevity()
    memory = record_replay_longevity_memory()
    continuity_durable = (
        continuity.get("longevity_stable")
        and durability.get("persistence_stable")
        and velocity.get("momentum_bounded")
        and story.get("story_durable")
    )
    return {
        "continuity_longevity": continuity,
        "durability_projection": durability,
        "erosion_velocity": velocity,
        "story_longevity": story,
        "memory": memory,
        "continuity_durable": continuity_durable,
        "summary": story.get("summary", "Replay longevity forecasting active."),
    }
