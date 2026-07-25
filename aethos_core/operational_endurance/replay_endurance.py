# SPDX-License-Identifier: Apache-2.0
"""Replay endurance — replay continuity persistence."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_erosion_intelligence.replay_resilience_decay import assess_replay_resilience_decay


def assess_replay_endurance() -> dict[str, Any]:
    replay = assess_replay_resilience_decay()
    return {
        **replay,
        "enduring": replay.get("decay_bounded", True),
        "summary": "Replay continuity persistence within durable bounds.",
    }
