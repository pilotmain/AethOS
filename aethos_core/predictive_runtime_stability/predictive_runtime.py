# SPDX-License-Identifier: Apache-2.0
"""Predictive runtime — forecasting orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.predictive_runtime_stability.long_tail_projection import project_future_stability
from aethos_core.predictive_runtime_stability.replay_projection import project_replay_persistence
from aethos_core.predictive_runtime_stability.resilience_decay_projection import project_resilience_erosion
from aethos_core.predictive_runtime_stability.stability_memory import record_predictive_stability_memory
from aethos_core.predictive_runtime_stability.trust_decay_projection import project_operational_trust_decay


def orchestrate_predictive_stability() -> dict[str, Any]:
    long_tail = project_future_stability()
    resilience = project_resilience_erosion()
    trust = project_operational_trust_decay()
    replay = project_replay_persistence()
    memory = record_predictive_stability_memory(stable=long_tail.get("projection_stable", False))
    stable = long_tail.get("projection_stable") and trust.get("fragility_bounded")
    return {
        "long_tail_projection": long_tail,
        "resilience_decay_projection": resilience,
        "trust_decay_projection": trust,
        "replay_projection": replay,
        "memory": memory,
        "stability_projected": stable,
        "summary": "Predictive runtime stability forecasting active — future trajectories evaluated.",
    }
