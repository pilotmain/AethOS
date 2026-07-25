# SPDX-License-Identifier: Apache-2.0
"""Replay erosion forecasting aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_erosion_forecasting.replay_forecast_runtime import orchestrate_replay_forecast


def assess_replay_erosion_forecasting() -> dict[str, Any]:
    forecast = orchestrate_replay_forecast()
    return {"ok": True, **forecast}
