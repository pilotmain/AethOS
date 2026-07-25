# SPDX-License-Identifier: Apache-2.0
"""Fragility confidence decay — erosion-aware confidence."""

from __future__ import annotations

from typing import Any

from aethos_core.infrastructure_fragility.replay_fragility import assess_replay_fragility


def assess_fragility_confidence_decay() -> dict[str, Any]:
    replay = assess_replay_fragility()
    bounded = not replay.get("fragile", False)
    return {
        "fragility_bounded": bounded,
        "summary": "Fragility-sensitive confidence erosion bounded." if bounded else "Fragility-sensitive confidence decay detected.",
    }
