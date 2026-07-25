# SPDX-License-Identifier: Apache-2.0
"""Fatigue runtime — fatigue orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_fatigue_intelligence.fatigue_memory import record_fatigue_memory
from aethos_core.operational_fatigue_intelligence.operational_strain import assess_operational_strain
from aethos_core.operational_fatigue_intelligence.replay_fatigue import assess_replay_fatigue
from aethos_core.operational_fatigue_intelligence.stabilization_fatigue import assess_stabilization_fatigue
from aethos_core.operational_fatigue_intelligence.verification_fatigue import assess_verification_fatigue


def orchestrate_operational_fatigue() -> dict[str, Any]:
    replay = assess_replay_fatigue()
    verification = assess_verification_fatigue()
    stabilization = assess_stabilization_fatigue()
    strain = assess_operational_strain()
    memory = record_fatigue_memory(score=strain.get("fatigue_score", 0.33))
    fatigued = replay.get("strained") or verification.get("exhausted") or strain.get("accelerating")
    return {
        "replay_fatigue": replay,
        "verification_fatigue": verification,
        "stabilization_fatigue": stabilization,
        "operational_strain": strain,
        "memory": memory,
        "fatigue_elevated": fatigued,
        "summary": stabilization.get("summary", "Operational fatigue intelligence active."),
    }
