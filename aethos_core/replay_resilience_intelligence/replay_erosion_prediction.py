# SPDX-License-Identifier: Apache-2.0
"""Replay erosion prediction — replay decay forecasting."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_persistence.replay_erosion_detection import detect_replay_erosion


def predict_replay_erosion() -> dict[str, Any]:
    erosion = detect_replay_erosion()
    return {
        **erosion,
        "escalation_risk": erosion.get("erosion_detected", False),
        "summary": "No significant replay erosion trajectories forecast." if not erosion.get("erosion_detected") else "Replay erosion escalation risk detected.",
    }
