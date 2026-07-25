# SPDX-License-Identifier: Apache-2.0
"""Replay decay tracking — replay instability."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_decay.replay_erosion import assess_replay_erosion


def track_replay_decay() -> dict[str, Any]:
    return assess_replay_erosion()
