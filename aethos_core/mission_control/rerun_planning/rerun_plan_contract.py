# SPDX-License-Identifier: Apache-2.0
"""FIX 138 — governed rerun plan contract (planning only)."""

from __future__ import annotations

from typing import Final

RERUN_PLAN_SCHEMA_VERSION: Final[str] = "mission_control_rerun_plan_v1"
RERUN_PLAN_FIX: Final[str] = "FIX 138"
MUTATION_PERFORMED_FIX_138: Final[bool] = False
RERUN_EXECUTION_ENABLED_FIX_138: Final[bool] = False

RERUN_PLAN_ROUTE_ID: Final[str] = "mission_control_rerun_plan"

RERUN_PLAN_INVARIANT: Final[str] = (
    "governed_rerun_planning_is_chat_only_no_rerun_execution_until_explicit_future_fix"
)

# Hypothetical operator phrases for documentation — not executable in FIX 138.
RERUN_PLAN_PHRASE_TEMPLATE: Final[str] = (
    "plan governed mission rerun from {gate_id} for session {session_id}"
)
