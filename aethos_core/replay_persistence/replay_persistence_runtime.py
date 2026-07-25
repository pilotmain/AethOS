# SPDX-License-Identifier: Apache-2.0
"""Replay persistence runtime — replay orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_persistence.replay_erosion_detection import detect_replay_erosion
from aethos_core.replay_persistence.replay_persistence_memory import record_replay_persistence_memory
from aethos_core.replay_persistence.replay_recovery_tracking import track_replay_recovery
from aethos_core.replay_persistence.replay_resilience import assess_replay_resilience
from aethos_core.replay_persistence.replay_story_evolution import evolve_replay_story


def orchestrate_replay_persistence() -> dict[str, Any]:
    erosion = detect_replay_erosion()
    recovery = track_replay_recovery()
    resilience = assess_replay_resilience()
    story = evolve_replay_story(stable=not erosion.get("erosion_detected"))
    memory = record_replay_persistence_memory(stable=resilience.get("resilient", False))
    persistent = resilience.get("resilient") and not erosion.get("erosion_detected")
    return {
        "erosion_detection": erosion,
        "recovery_tracking": recovery,
        "resilience": resilience,
        "story": story,
        "memory": memory,
        "persistent": persistent,
        "summary": story.get("narrative", "Replay persistence cognition active."),
    }
