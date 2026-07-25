# SPDX-License-Identifier: Apache-2.0
"""Replay fragility — replay instability risk."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_persistence.replay_erosion_detection import detect_replay_erosion


def assess_replay_fragility() -> dict[str, Any]:
    erosion = detect_replay_erosion()
    fragile = erosion.get("erosion_detected", False)
    return {
        **erosion,
        "fragile": fragile,
        "summary": "Replay instability risk elevated." if fragile else "Replay fragility within acceptable bounds.",
    }
