# SPDX-License-Identifier: Apache-2.0
"""FIX 146 — mission orchestration contract (coordination cognition without execution)."""

from __future__ import annotations

from typing import Final

MISSION_ORCHESTRATION_SCHEMA_VERSION: Final[str] = "mission_control_mission_orchestration_v1"
MISSION_ORCHESTRATION_FIX: Final[str] = "FIX 146"
MUTATION_PERFORMED_FIX_146: Final[bool] = False
AUTONOMOUS_SEQUENCING_EXECUTION_ENABLED_FIX_146: Final[bool] = False
AUTONOMOUS_APPROVAL_BATCHING_ENABLED_FIX_146: Final[bool] = False
AUTONOMOUS_PROMOTION_DEPLOY_ENABLED_FIX_146: Final[bool] = False
AUTONOMOUS_ORCHESTRATION_ENABLED_FIX_146: Final[bool] = False

MISSION_ORCHESTRATION_ROUTE_ID: Final[str] = "mission_control_mission_orchestration"

MISSION_ORCHESTRATION_INVARIANT: Final[str] = (
    "mission_orchestration_is_read_only_coordination_cognition_no_autonomous_sequencing_or_execution"
)

ORCHESTRATION_RECOMMENDATION_EXECUTABLE: Final[bool] = False
