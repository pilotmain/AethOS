# SPDX-License-Identifier: Apache-2.0
"""Replay resilience memory — replay durability."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_resilience_memory.replay_resilience_memory import recall_replay_resilience_memory


def recall_replay_durability(*, stable: bool = True) -> dict[str, Any]:
    return recall_replay_resilience_memory(stable=stable)
