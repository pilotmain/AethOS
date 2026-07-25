# SPDX-License-Identifier: Apache-2.0
"""Replay pressure tracking — replay stress evolution."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_resilience_intelligence.replay_pressure_tracking import track_replay_pressure


def track_replay_stress() -> dict[str, Any]:
    return track_replay_pressure()
