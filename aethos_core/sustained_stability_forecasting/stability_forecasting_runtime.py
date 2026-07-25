# SPDX-License-Identifier: Apache-2.0
"""Stability forecasting runtime — forecasting orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_stability_forecasting.long_tail_projection import project_long_tail_stability
from aethos_core.sustained_stability_forecasting.replay_durability_projection import project_replay_durability
from aethos_core.sustained_stability_forecasting.resilience_decay_projection import project_resilience_decay
from aethos_core.sustained_stability_forecasting.stability_memory import record_stability_memory
from aethos_core.sustained_stability_forecasting.trust_decay_projection import project_trust_decay


def orchestrate_stability_forecasting() -> dict[str, Any]:
    long_tail = project_long_tail_stability()
    resilience_decay = project_resilience_decay()
    trust_decay = project_trust_decay()
    replay = project_replay_durability()
    memory = record_stability_memory(stable=long_tail.get("projection_stable", False))
    stable = long_tail.get("projection_stable") and trust_decay.get("fragility_bounded")
    return {
        "long_tail_projection": long_tail,
        "resilience_decay_projection": resilience_decay,
        "trust_decay_projection": trust_decay,
        "replay_durability_projection": replay,
        "memory": memory,
        "stability_projected": stable,
        "summary": "Long-tail stability forecasting active — future operational trajectories evaluated.",
    }
