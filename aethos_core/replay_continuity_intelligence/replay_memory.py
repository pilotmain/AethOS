# SPDX-License-Identifier: Apache-2.0
"""Replay memory — replay operational memory."""

from __future__ import annotations

from typing import Any

_MEMORY: list[dict[str, Any]] = []


def record_replay_memory(*, stable: bool) -> dict[str, Any]:
    entry = {"stable": stable}
    _MEMORY.append(entry)
    if len(_MEMORY) > 50:
        del _MEMORY[:-50]
    return {"memory_count": len(_MEMORY), "latest": entry}
