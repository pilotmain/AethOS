# SPDX-License-Identifier: Apache-2.0
"""Replay resilience decay — replay durability erosion."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_erosion_forecasting.replay_durability_decay import assess_replay_durability_decay


def assess_replay_resilience_decay() -> dict[str, Any]:
    return assess_replay_durability_decay()
