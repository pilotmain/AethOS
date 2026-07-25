# SPDX-License-Identifier: Apache-2.0
"""Replay stability tracking — replay resilience."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_operational_decay.replay_decay_tracking import track_replay_decay


def track_replay_stability_long_tail() -> dict[str, Any]:
    return track_replay_decay()
