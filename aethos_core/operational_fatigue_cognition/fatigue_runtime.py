# SPDX-License-Identifier: Apache-2.0
"""Fatigue runtime — fatigue orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_fatigue_cognition.fatigue_memory import record_fatigue_trajectory
from aethos_core.operational_fatigue_cognition.operational_exhaustion import assess_operational_exhaustion
from aethos_core.operational_fatigue_cognition.replay_fatigue import assess_replay_strain
from aethos_core.operational_fatigue_cognition.stabilization_pressure import assess_stabilization_pressure
from aethos_core.operational_fatigue_cognition.verification_fatigue import assess_verification_exhaustion


def orchestrate_operational_fatigue() -> dict[str, Any]:
    replay = assess_replay_strain()
    verification = assess_verification_exhaustion()
    stabilization = assess_stabilization_pressure()
    exhaustion = assess_operational_exhaustion()
    memory = record_fatigue_trajectory(score=exhaustion.get("fatigue_score", 0.34))
    fatigued = replay.get("strained") or verification.get("exhausted") or exhaustion.get("accelerating")
    return {
        "replay_fatigue": replay,
        "verification_fatigue": verification,
        "stabilization_pressure": stabilization,
        "operational_exhaustion": exhaustion,
        "memory": memory,
        "fatigue_elevated": fatigued,
        "summary": stabilization.get("summary", "Operational fatigue cognition active."),
    }
