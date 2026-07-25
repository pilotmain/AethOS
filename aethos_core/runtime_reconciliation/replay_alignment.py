# SPDX-License-Identifier: Apache-2.0
"""Replay alignment — replay continuity convergence."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_verification.replay_stability import assess_replay_stability


def assess_replay_alignment() -> dict[str, Any]:
    replay = assess_replay_stability()
    return {
        **replay,
        "aligned": replay.get("replay_stable", False),
        "summary": "Replay continuity aligned across operational windows." if replay.get("replay_stable") else "Replay continuity alignment monitoring active.",
    }
