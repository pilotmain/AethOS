# SPDX-License-Identifier: Apache-2.0
"""Replay survivability runtime — orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_continuity_survivability.replay_continuity_projection import project_replay_continuity
from aethos_core.replay_continuity_survivability.replay_longevity_projection import project_replay_longevity
from aethos_core.replay_continuity_survivability.replay_story_survivability import assess_replay_story_survivability
from aethos_core.replay_continuity_survivability.replay_survivability_decay import assess_replay_survivability_decay
from aethos_core.replay_continuity_survivability.replay_survivability_memory import record_replay_survivability_memory


def orchestrate_replay_continuity_survivability() -> dict[str, Any]:
    continuity = project_replay_continuity()
    longevity = project_replay_longevity()
    decay = assess_replay_survivability_decay()
    story = assess_replay_story_survivability()
    memory = record_replay_survivability_memory()
    continuity_sustainable = (
        continuity.get("continuity_sustainable")
        and longevity.get("continuity_sustainable")
        and decay.get("decay_bounded")
        and story.get("story_sustainable")
    )
    return {
        "continuity_projection": continuity,
        "longevity_projection": longevity,
        "survivability_decay": decay,
        "story_survivability": story,
        "memory": memory,
        "continuity_sustainable": continuity_sustainable,
        "summary": story.get("summary", "Replay continuity survivability active."),
    }
