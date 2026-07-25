# SPDX-License-Identifier: Apache-2.0
"""FIX 128 — Mission Control cross-lane observability contract (read-only)."""

from __future__ import annotations

from typing import Final

CROSS_LANE_SCHEMA_VERSION: Final[str] = "mission_control_cross_lane_v1"
CROSS_LANE_FIX: Final[str] = "FIX 128"
MISSION_CONTROL_ROUTE_ID: Final[str] = "mission_control_cross_lane"

MUTATION_PERFORMED_FIX_128: Final[bool] = False
LANE_MUTATION_ENABLED_FIX_128: Final[bool] = False

OBSERVED_LANES: Final[tuple[str, ...]] = (
    "railway_orchestration",
    "software_delivery",
    "production_governance",
    "incident_command",
    "multi_agent_collaboration",
    "route_diagnostics",
    "durable_jobs",
)

ARCHITECTURE_BOUNDARY: Final[str] = (
    "software_delivery_lane != infrastructure_mutation_lane != production_governance_lane"
)
