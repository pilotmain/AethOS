# SPDX-License-Identifier: Apache-2.0
"""Replay continuity intelligence aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_continuity_intelligence.continuity_reconstruction import reconstruct_continuity
from aethos_core.replay_continuity_intelligence.degradation_timelines import track_degradation_timeline
from aethos_core.replay_continuity_intelligence.replay_causality import analyze_replay_causality
from aethos_core.replay_continuity_intelligence.replay_memory import record_replay_memory
from aethos_core.replay_continuity_intelligence.replay_stability_tracking import track_replay_stability
from aethos_core.replay_continuity_intelligence.replay_storytelling import build_replay_story


def assess_replay_continuity_intelligence() -> dict[str, Any]:
    story = build_replay_story()
    continuity = reconstruct_continuity()
    timeline = track_degradation_timeline()
    causality = analyze_replay_causality()
    stability = track_replay_stability()
    memory = record_replay_memory(stable=bool(stability.get("replay_stable")))
    stable = bool(story.get("replay_converged")) and timeline.get("timeline_stage") == "bounded"
    return {
        "ok": True,
        "replay_story": story,
        "continuity_reconstruction": continuity,
        "degradation_timeline": timeline,
        "replay_causality": causality,
        "stability_tracking": stability,
        "replay_memory": memory,
        "continuity_stable": stable,
        "summary": story.get("narrative", "Replay continuity intelligence active."),
    }
