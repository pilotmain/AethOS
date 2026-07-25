# SPDX-License-Identifier: Apache-2.0
"""Replay longevity memory — replay operational history."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_erosion_intelligence.replay_memory import record_replay_erosion_memory


def record_replay_longevity_memory() -> dict[str, Any]:
    return record_replay_erosion_memory(stable=True)
