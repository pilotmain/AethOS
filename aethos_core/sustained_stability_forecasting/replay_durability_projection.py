# SPDX-License-Identifier: Apache-2.0
"""Replay durability projection — replay persistence."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_erosion_forecasting.replay_durability_decay import assess_replay_durability_decay


def project_replay_durability() -> dict[str, Any]:
    return assess_replay_durability_decay()
