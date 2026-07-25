# SPDX-License-Identifier: Apache-2.0
"""Replay forecasting — replay erosion risk."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_resilience_intelligence.replay_erosion_prediction import predict_replay_erosion


def forecast_replay_erosion() -> dict[str, Any]:
    erosion = predict_replay_erosion()
    moderate_pressure = not erosion.get("escalation_risk", False)
    return {
        **erosion,
        "moderate_pressure": moderate_pressure,
        "summary": (
            "Replay persistence remains resilient across current operational verification windows, "
            "though moderate replay erosion pressure is beginning to emerge under sustained runtime activity."
        )
        if not erosion.get("escalation_risk")
        else "Replay erosion risk elevated — forecasting active.",
    }
