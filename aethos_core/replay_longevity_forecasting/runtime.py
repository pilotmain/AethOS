# SPDX-License-Identifier: Apache-2.0
"""Replay longevity forecasting aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_longevity_forecasting.replay_longevity_runtime import orchestrate_replay_longevity


def assess_replay_longevity_forecasting() -> dict[str, Any]:
    longevity = orchestrate_replay_longevity()
    return {"ok": True, **longevity}
