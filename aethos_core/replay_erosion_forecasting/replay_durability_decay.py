# SPDX-License-Identifier: Apache-2.0
"""Replay durability decay — replay resilience decay."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_resilience.replay_recovery_resilience import assess_replay_recovery_resilience


def assess_replay_durability_decay() -> dict[str, Any]:
    recovery = assess_replay_recovery_resilience()
    decay_bounded = recovery.get("durable", False)
    return {
        **recovery,
        "decay_bounded": decay_bounded,
        "summary": "Replay resilience decay bounded." if decay_bounded else "Replay durability decay emerging.",
    }
