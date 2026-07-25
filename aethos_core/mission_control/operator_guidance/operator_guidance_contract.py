# SPDX-License-Identifier: Apache-2.0
"""FIX 142 — operator contextual guidance contract (recommendation-only)."""

from __future__ import annotations

from typing import Final

OPERATOR_GUIDANCE_SCHEMA_VERSION: Final[str] = "mission_control_operator_guidance_v1"
OPERATOR_GUIDANCE_FIX: Final[str] = "FIX 142"
MUTATION_PERFORMED_FIX_142: Final[bool] = False
AUTONOMOUS_EXECUTION_ENABLED_FIX_142: Final[bool] = False
AUTOMATIC_MUTATION_PLANNING_ENABLED_FIX_142: Final[bool] = False

OPERATOR_GUIDANCE_ROUTE_ID: Final[str] = "mission_control_operator_guidance"

OPERATOR_GUIDANCE_INVARIANT: Final[str] = (
    "operator_guidance_is_recommendation_only_executable_false_operator_approved_only"
)

RECOMMENDATION_EXECUTABLE: Final[bool] = False
OPERATOR_APPROVAL_REQUIRED: Final[bool] = True
