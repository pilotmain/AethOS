# SPDX-License-Identifier: Apache-2.0
"""FIX 147 — mission readiness review board contract."""

from __future__ import annotations

from typing import Final

MISSION_READINESS_REVIEW_SCHEMA_VERSION: Final[str] = "mission_control_mission_readiness_review_v1"
MISSION_READINESS_REVIEW_FIX: Final[str] = "FIX 147"
MUTATION_PERFORMED_FIX_147: Final[bool] = False
AUTONOMOUS_GO_NO_GO_EXECUTION_ENABLED_FIX_147: Final[bool] = False
AUTONOMOUS_READINESS_DECISION_ENABLED_FIX_147: Final[bool] = False
EXECUTION_AUTHORITY_DELEGATED_FIX_147: Final[bool] = False

MISSION_READINESS_REVIEW_ROUTE_ID: Final[str] = "mission_control_mission_readiness_review"

MISSION_READINESS_REVIEW_INVARIANT: Final[str] = (
    "mission_readiness_review_is_read_only_human_reviewable_advisory_no_execution_authority"
)

HUMAN_REVIEW_REQUIRED_FIX_147: Final[bool] = True
READINESS_RECOMMENDATION_EXECUTABLE: Final[bool] = False

GO_NO_GO_HOLD_VALUES: Final[tuple[str, ...]] = ("go", "no-go", "hold")
