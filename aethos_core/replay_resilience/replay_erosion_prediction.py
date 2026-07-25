# SPDX-License-Identifier: Apache-2.0
"""Replay erosion prediction — replay degradation forecasting."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_resilience_intelligence.replay_erosion_prediction import predict_replay_erosion


def forecast_replay_erosion() -> dict[str, Any]:
    return predict_replay_erosion()
