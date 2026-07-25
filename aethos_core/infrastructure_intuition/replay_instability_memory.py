# SPDX-License-Identifier: Apache-2.0
"""Replay instability memory — replay degradation history."""

from __future__ import annotations

from typing import Any

_HISTORY: list[dict[str, Any]] = []


def record_replay_instability(*, stable: bool) -> dict[str, Any]:
    entry = {"stable": stable}
    _HISTORY.append(entry)
    if len(_HISTORY) > 50:
        del _HISTORY[:-50]
    return {"replay_history_count": len(_HISTORY), "latest": entry}
