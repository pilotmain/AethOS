# SPDX-License-Identifier: Apache-2.0
"""Resilience confidence — resilience weighting."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_resilience_cognition.resilience_trajectories import track_resilience_trajectories


def assess_resilience_confidence() -> dict[str, Any]:
    trajectories = track_resilience_trajectories()
    score = float(trajectories.get("current_score") or 0.87)
    return {"resilience_confidence": score, "summary": "Resilience confidence stable." if score >= 0.75 else "Resilience confidence monitoring active."}
