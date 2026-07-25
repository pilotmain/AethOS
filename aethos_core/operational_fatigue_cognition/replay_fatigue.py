# SPDX-License-Identifier: Apache-2.0
"""Replay fatigue — replay strain accumulation."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_fatigue_intelligence.replay_fatigue import assess_replay_fatigue


def assess_replay_strain() -> dict[str, Any]:
    return assess_replay_fatigue()
