# SPDX-License-Identifier: Apache-2.0
"""Replay acceleration — replay degradation velocity."""

from __future__ import annotations

from typing import Any

from aethos_core.fragility_acceleration.replay_acceleration import detect_replay_acceleration


def measure_replay_acceleration() -> dict[str, Any]:
    return detect_replay_acceleration()
