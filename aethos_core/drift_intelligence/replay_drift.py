# SPDX-License-Identifier: Apache-2.0
"""Replay drift — replay continuity degradation."""

from __future__ import annotations

from typing import Any


def assess_replay_drift(*, memory: dict[str, Any]) -> dict[str, Any]:
    replay_events = [e for e in (memory.get("entries") or []) if "replay" in str(e).lower()]
    degraded = len(replay_events) > 0 or memory.get("count", 0) > 5
    return {
        "replay_continuity_degraded": degraded,
        "replay_event_count": len(replay_events),
        "summary": "Replay continuity stable." if not degraded else "Recurring replay continuity degradation detected.",
    }
