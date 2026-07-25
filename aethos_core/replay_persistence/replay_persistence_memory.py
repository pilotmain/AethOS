# SPDX-License-Identifier: Apache-2.0
"""Replay persistence memory — replay operational memory."""

from __future__ import annotations

from typing import Any

from aethos_core.infrastructure_intuition.replay_instability_memory import record_replay_instability


def record_replay_persistence_memory(*, stable: bool = True) -> dict[str, Any]:
    return record_replay_instability(stable=stable)
