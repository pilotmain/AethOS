# SPDX-License-Identifier: Apache-2.0
"""Continuity longevity — replay continuity lifespan."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_operational_forecasting.replay_longevity_projection import project_replay_longevity


def assess_continuity_longevity() -> dict[str, Any]:
    return project_replay_longevity()
