# SPDX-License-Identifier: Apache-2.0
"""Replay persistence — replay stability."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_verification.replay_stability import assess_replay_stability


def assess_replay_persistence() -> dict[str, Any]:
    replay = assess_replay_stability()
    return {
        **replay,
        "persistent": replay.get("replay_stable", False),
        "summary": "Replay persistence stable across evolving runtime conditions." if replay.get("replay_stable") else "Replay persistence monitoring active.",
    }
