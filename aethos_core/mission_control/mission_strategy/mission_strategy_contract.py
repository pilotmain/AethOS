# SPDX-License-Identifier: Apache-2.0
"""FIX 145 — mission strategy contract (strategic cognition without autonomy)."""

from __future__ import annotations

from typing import Final

MISSION_STRATEGY_SCHEMA_VERSION: Final[str] = "mission_control_mission_strategy_v1"
MISSION_STRATEGY_FIX: Final[str] = "FIX 145"
MUTATION_PERFORMED_FIX_145: Final[bool] = False
AUTONOMOUS_PLANNING_ENABLED_FIX_145: Final[bool] = False
AUTONOMOUS_EXECUTION_ENABLED_FIX_145: Final[bool] = False
AUTONOMOUS_REPRIORITIZATION_ENABLED_FIX_145: Final[bool] = False
ORGANIZATIONAL_SELF_DIRECTION_ENABLED_FIX_145: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_145: Final[bool] = False

MISSION_STRATEGY_ROUTE_ID: Final[str] = "mission_control_mission_strategy"

MISSION_STRATEGY_INVARIANT: Final[str] = (
    "mission_strategy_is_read_only_strategic_reasoning_no_autonomous_planning_or_self_direction"
)

STRATEGY_RECOMMENDATION_EXECUTABLE: Final[bool] = False
