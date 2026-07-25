# SPDX-License-Identifier: Apache-2.0
"""Replay resilience memory — replay history."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_persistence.replay_persistence_memory import record_replay_persistence_memory


def record_replay_resilience_memory(*, stable: bool = True) -> dict[str, Any]:
    return record_replay_persistence_memory(stable=stable)
