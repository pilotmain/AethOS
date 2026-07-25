# SPDX-License-Identifier: Apache-2.0
"""Replay survivability memory — replay survivability history."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_erosion_intelligence.replay_memory import record_replay_erosion_memory


def record_replay_survivability_memory() -> dict[str, Any]:
    return record_replay_erosion_memory(stable=True)
