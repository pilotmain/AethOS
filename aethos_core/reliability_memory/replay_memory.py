# SPDX-License-Identifier: Apache-2.0
"""Replay memory — continuity degradation history."""

from __future__ import annotations

from typing import Any

_REPLAY_MEMORY: list[dict[str, Any]] = []


def record_replay_event(*, entry: dict[str, Any]) -> None:
    _REPLAY_MEMORY.append(entry)
    if len(_REPLAY_MEMORY) > 80:
        del _REPLAY_MEMORY[:-80]


def replay_memory_state() -> dict[str, Any]:
    return {"entries": list(_REPLAY_MEMORY[-10:]), "count": len(_REPLAY_MEMORY)}
