# SPDX-License-Identifier: Apache-2.0
"""Long-tail stability aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_stability.delayed_degradation import detect_delayed_degradation
from aethos_core.long_tail_stability.instability_oscillation import detect_instability_oscillation
from aethos_core.long_tail_stability.recovery_fragility import detect_recovery_fragility
from aethos_core.long_tail_stability.replay_stability_tracking import track_replay_stability_long_tail
from aethos_core.long_tail_stability.sustained_operational_memory import recall_sustained_operational_memory
from aethos_core.long_tail_stability.topology_instability import detect_topology_instability


def assess_long_tail_stability(*, provider: str = "railway") -> dict[str, Any]:
    oscillation = detect_instability_oscillation()
    delayed = detect_delayed_degradation()
    fragility = detect_recovery_fragility()
    topology = detect_topology_instability()
    replay = track_replay_stability_long_tail()
    memory = recall_sustained_operational_memory(provider=provider)
    stable = (
        not oscillation.get("oscillating")
        and delayed.get("decay_bounded", True)
        and not fragility.get("fragile")
        and not topology.get("unstable")
    )
    return {
        "ok": True,
        "instability_oscillation": oscillation,
        "delayed_degradation": delayed,
        "recovery_fragility": fragility,
        "topology_instability": topology,
        "replay_stability": replay,
        "operational_memory": memory,
        "long_tail_stable": stable,
        "summary": "Long-tail stability intelligence active — no significant delayed degradation trajectories emerging."
        if stable
        else "Long-tail stability monitoring active across extended runtime periods.",
    }
