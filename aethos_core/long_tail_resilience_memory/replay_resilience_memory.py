# SPDX-License-Identifier: Apache-2.0
"""Replay resilience memory — replay durability."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_operational_memory.replay_erosion_memory import recall_replay_erosion


def recall_replay_resilience_memory(*, stable: bool = True) -> dict[str, Any]:
    return recall_replay_erosion(stable=stable)
