# SPDX-License-Identifier: Apache-2.0
"""FIX 143 — meta-governance insights contract (insight-only)."""

from __future__ import annotations

from typing import Final

GOVERNANCE_INSIGHTS_SCHEMA_VERSION: Final[str] = "mission_control_governance_insights_v1"
GOVERNANCE_INSIGHTS_FIX: Final[str] = "FIX 143"
MUTATION_PERFORMED_FIX_143: Final[bool] = False
POLICY_AUTO_TUNING_ENABLED_FIX_143: Final[bool] = False
GOVERNANCE_SELF_MODIFICATION_ENABLED_FIX_143: Final[bool] = False
AUTONOMOUS_OPTIMIZATION_ENABLED_FIX_143: Final[bool] = False

GOVERNANCE_INSIGHTS_ROUTE_ID: Final[str] = "mission_control_governance_insights"

GOVERNANCE_INSIGHTS_INVARIANT: Final[str] = (
    "governance_insights_are_read_only_no_policy_auto_tuning_or_self_modifying_governance"
)

INSIGHT_EXECUTABLE: Final[bool] = False
