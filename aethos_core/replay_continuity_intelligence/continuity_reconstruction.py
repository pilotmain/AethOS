# SPDX-License-Identifier: Apache-2.0
"""Continuity reconstruction — recovery journeys."""

from __future__ import annotations

from typing import Any

from aethos_core.recovery_truth_convergence.replay_recovery import assess_replay_recovery


def reconstruct_continuity() -> dict[str, Any]:
    recovery = assess_replay_recovery()
    return {
        **recovery,
        "journey_stage": "stabilizing" if recovery.get("aligned") else "monitoring",
    }
