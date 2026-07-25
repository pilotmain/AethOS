# SPDX-License-Identifier: Apache-2.0
"""Forecasting runtime — orchestration aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_operational_forecasting.forecasting_memory import record_forecasting_memory
from aethos_core.long_tail_operational_forecasting.operational_trajectory_projection import project_operational_trajectory
from aethos_core.long_tail_operational_forecasting.replay_longevity_projection import project_replay_longevity
from aethos_core.long_tail_operational_forecasting.survivability_projection import project_survivability
from aethos_core.long_tail_operational_forecasting.topology_sustainability_projection import project_topology_sustainability


def orchestrate_long_tail_forecasting(*, provider: str = "railway") -> dict[str, Any]:
    trajectory = project_operational_trajectory()
    survivability = project_survivability()
    replay = project_replay_longevity()
    topology = project_topology_sustainability()
    memory = record_forecasting_memory(survivable=survivability.get("survivable", False))
    forecastable = (
        trajectory.get("projection_stable")
        and survivability.get("survivable")
        and replay.get("longevity_stable")
    )
    return {
        "operational_trajectory": trajectory,
        "survivability_projection": survivability,
        "replay_longevity": replay,
        "topology_sustainability": topology,
        "memory": memory,
        "forecastable": forecastable,
        "summary": replay.get("summary", "Long-tail operational forecasting active."),
    }
