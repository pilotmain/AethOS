# SPDX-License-Identifier: Apache-2.0
"""Replay pressure projection — replay stress projection."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_resilience.replay_pressure_tracking import track_replay_stress


def project_replay_pressure() -> dict[str, Any]:
    return track_replay_stress()
