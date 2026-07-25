# SPDX-License-Identifier: Apache-2.0
"""Replay resilience — replay durability."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_verification.replay_stability import assess_replay_stability


def assess_replay_resilience() -> dict[str, Any]:
    replay = assess_replay_stability(continuity_score=0.83)
    resilient = replay.get("replay_stable", False)
    return {
        **replay,
        "resilient": resilient,
        "summary": "Replay durability stable across sustained verification windows." if resilient else "Replay resilience monitoring active.",
    }
