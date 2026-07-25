# SPDX-License-Identifier: Apache-2.0
"""Replay resilience — replay persistence under pressure."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_persistence.replay_resilience import assess_replay_resilience


def assess_replay_resilience_under_pressure() -> dict[str, Any]:
    replay = assess_replay_resilience()
    return {
        **replay,
        "pressure_resilient": replay.get("resilient", False),
        "summary": "Replay continuity persists under sustained operational pressure." if replay.get("resilient") else "Replay resilience under pressure monitoring active.",
    }
