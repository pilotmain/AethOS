# SPDX-License-Identifier: Apache-2.0
"""Replay exhaustion — replay fatigue accumulation."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_fatigue_intelligence.replay_fatigue import assess_replay_fatigue


def assess_replay_exhaustion() -> dict[str, Any]:
    fatigue = assess_replay_fatigue()
    return {
        **fatigue,
        "exhaustion_emerging": fatigue.get("strained", False),
        "summary": "Replay fatigue accumulation within durable bounds.",
    }
