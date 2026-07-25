# SPDX-License-Identifier: Apache-2.0
"""Replay erosion memory — replay degradation."""

from __future__ import annotations

from typing import Any

from aethos_core.infrastructure_intuition.replay_instability_memory import record_replay_instability


def recall_replay_erosion(*, stable: bool = True) -> dict[str, Any]:
    return record_replay_instability(stable=stable)
