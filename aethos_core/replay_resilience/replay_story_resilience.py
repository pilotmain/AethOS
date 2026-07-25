# SPDX-License-Identifier: Apache-2.0
"""Replay story resilience — operational replay narratives."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_resilience_intelligence.replay_story_resilience import build_replay_resilience_story


def build_replay_narrative(*, resilient: bool = True) -> dict[str, Any]:
    story = build_replay_resilience_story(resilient=resilient)
    return {
        **story,
        "narrative": (
            "Replay persistence remains resilient across sustained operational verification windows, "
            "with no significant replay erosion trajectories currently emerging under runtime pressure."
        )
        if resilient
        else story.get("narrative", "Replay resilience evolution under observation."),
    }
