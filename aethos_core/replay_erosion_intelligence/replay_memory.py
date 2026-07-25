# SPDX-License-Identifier: Apache-2.0
"""Replay memory — replay degradation history."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_resilience.replay_memory import record_replay_memory


def record_replay_erosion_memory(*, stable: bool = True) -> dict[str, Any]:
    return record_replay_memory(stable=stable)
