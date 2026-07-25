# SPDX-License-Identifier: Apache-2.0
"""Replay durability confidence — replay trust."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_persistence.replay_resilience import assess_replay_resilience


def assess_replay_durability_confidence() -> dict[str, Any]:
    replay = assess_replay_resilience()
    score = float(replay.get("continuity_score") or 0.84)
    return {"replay_durability_confidence": score, "summary": "Replay durability trust stable." if score >= 0.75 else "Replay durability trust monitoring active."}
