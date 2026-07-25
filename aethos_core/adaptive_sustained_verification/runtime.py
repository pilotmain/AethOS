# SPDX-License-Identifier: Apache-2.0
"""Adaptive sustained verification aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.adaptive_sustained_verification.adaptive_verification_runtime import run_adaptive_verification
from aethos_core.adaptive_sustained_verification.dependency_reverification import run_dependency_reverification
from aethos_core.adaptive_sustained_verification.infrastructure_reverification import run_infrastructure_reverification
from aethos_core.adaptive_sustained_verification.operational_pressure_windows import assess_operational_pressure_windows
from aethos_core.adaptive_sustained_verification.replay_reverification import run_replay_reverification
from aethos_core.adaptive_sustained_verification.verification_decay_tracking import track_verification_decay


def assess_adaptive_sustained_verification() -> dict[str, Any]:
    verification = run_adaptive_verification()
    pressure = assess_operational_pressure_windows()
    replay = run_replay_reverification()
    dependency = run_dependency_reverification()
    infrastructure = run_infrastructure_reverification()
    decay = track_verification_decay()
    adaptive = verification.get("sustained") or decay.get("erosion_bounded", True)
    return {
        "ok": True,
        "adaptive_verification": verification,
        "pressure_windows": pressure,
        "replay_reverification": replay,
        "dependency_reverification": dependency,
        "infrastructure_reverification": infrastructure,
        "verification_decay": decay,
        "adaptively_qualified": adaptive,
        "summary": "Continuously adaptive operational trust verification active.",
    }
