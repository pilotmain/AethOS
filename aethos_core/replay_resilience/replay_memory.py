# SPDX-License-Identifier: Apache-2.0
"""Replay memory — replay resilience history."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_resilience_intelligence.replay_resilience_memory import record_replay_resilience_memory


def record_replay_memory(*, stable: bool = True) -> dict[str, Any]:
    return record_replay_resilience_memory(stable=stable)
