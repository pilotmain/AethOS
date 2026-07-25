# SPDX-License-Identifier: Apache-2.0
"""Replay recovery resilience — replay recovery durability."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_resilience_intelligence.replay_recovery_durability import assess_replay_recovery_durability


def assess_replay_recovery_resilience() -> dict[str, Any]:
    return assess_replay_recovery_durability()
