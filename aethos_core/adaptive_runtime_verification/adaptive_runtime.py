# SPDX-License-Identifier: Apache-2.0
"""Adaptive runtime — adaptive verification orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.adaptive_runtime_verification.adaptive_decay_detection import detect_adaptive_decay
from aethos_core.adaptive_runtime_verification.continuity_reverification import run_continuity_reverification
from aethos_core.adaptive_runtime_verification.pressure_aware_verification import run_pressure_aware_verification
from aethos_core.adaptive_runtime_verification.replay_adaptive_checks import run_replay_adaptive_checks
from aethos_core.adaptive_runtime_verification.topology_adaptive_verification import run_topology_adaptive_verification
from aethos_core.adaptive_sustained_verification.adaptive_verification_runtime import run_adaptive_verification


def orchestrate_adaptive_runtime(*, provider: str = "railway") -> dict[str, Any]:
    verification = run_adaptive_verification()
    pressure = run_pressure_aware_verification()
    continuity = run_continuity_reverification(provider=provider)
    replay = run_replay_adaptive_checks()
    topology = run_topology_adaptive_verification()
    decay = detect_adaptive_decay()
    adaptive = verification.get("sustained") or decay.get("erosion_bounded", True)
    return {
        "adaptive_verification": verification,
        "pressure_aware": pressure,
        "continuity_reverification": continuity,
        "replay_checks": replay,
        "topology_verification": topology,
        "decay_detection": decay,
        "adaptively_qualified": adaptive,
        "summary": "Verification adapts to evolving operational behavior — continuously adaptive trust verification active.",
    }
