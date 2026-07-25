# SPDX-License-Identifier: Apache-2.0
"""Replay resilience tracking — replay durability."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_resilience_intelligence.replay_pressure_tracking import track_replay_pressure


def track_replay_resilience() -> dict[str, Any]:
    replay = track_replay_pressure()
    return {
        **replay,
        "durable": replay.get("pressure_stable", False),
        "summary": "Replay durability held under operational stress." if replay.get("pressure_stable") else "Replay resilience tracking active.",
    }
