# SPDX-License-Identifier: Apache-2.0
"""Replay survivability decay — replay durability erosion."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_erosion_intelligence.replay_resilience_decay import assess_replay_resilience_decay


def assess_replay_survivability_decay() -> dict[str, Any]:
    decay = assess_replay_resilience_decay()
    return {
        **decay,
        "decay_bounded": decay.get("decay_bounded", True),
        "summary": "Replay survivability decay within durable bounds.",
    }
