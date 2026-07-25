# SPDX-License-Identifier: Apache-2.0
"""FIX 144 — governance simulation sandbox contract."""

from __future__ import annotations

from typing import Final

GOVERNANCE_SIMULATION_SCHEMA_VERSION: Final[str] = "mission_control_governance_simulation_v1"
GOVERNANCE_SIMULATION_FIX: Final[str] = "FIX 144"
MUTATION_PERFORMED_FIX_144: Final[bool] = False
LIVE_POLICY_MUTATION_ENABLED_FIX_144: Final[bool] = False
AUTO_POLICY_UPDATE_ENABLED_FIX_144: Final[bool] = False
AUTOMATIC_GOVERNANCE_TUNING_ENABLED_FIX_144: Final[bool] = False

GOVERNANCE_SIMULATION_ROUTE_ID: Final[str] = "mission_control_governance_simulation"

GOVERNANCE_SIMULATION_INVARIANT: Final[str] = (
    "governance_simulation_is_hypothetical_only_no_live_policy_mutation_or_auto_tuning"
)

SIMULATION_EXECUTABLE: Final[bool] = False

DEFAULT_SCENARIO_IDS: Final[tuple[str, ...]] = (
    "alternate_approval_chain",
    "reduced_quorum",
    "increased_quorum",
    "strict_rollout_policy",
    "stricter_verification",
    "alternate_gate_sequencing",
)
