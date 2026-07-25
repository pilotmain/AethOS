# SPDX-License-Identifier: Apache-2.0
"""Replay recovery durability — replay recovery persistence."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_persistence.replay_recovery_tracking import track_replay_recovery


def assess_replay_recovery_durability() -> dict[str, Any]:
    recovery = track_replay_recovery()
    durable = recovery.get("aligned", False)
    return {
        **recovery,
        "durable": durable,
        "summary": "Replay recovery persistence durable." if durable else "Replay recovery durability monitoring active.",
    }
