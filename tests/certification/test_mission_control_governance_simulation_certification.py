# SPDX-License-Identifier: Apache-2.0
"""FIX 144 — governance simulation certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.governance_simulation.governance_simulation_contract import (
    AUTOMATIC_GOVERNANCE_TUNING_ENABLED_FIX_144,
    AUTO_POLICY_UPDATE_ENABLED_FIX_144,
    GOVERNANCE_SIMULATION_FIX,
    GOVERNANCE_SIMULATION_SCHEMA_VERSION,
    LIVE_POLICY_MUTATION_ENABLED_FIX_144,
    MUTATION_PERFORMED_FIX_144,
    SIMULATION_EXECUTABLE,
)
from aethos_core.mission_control.governance_simulation.governance_simulation_service import run_governance_simulation
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-gov-sim-cert-144"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()


class TestMissionControlGovernanceSimulationCertification:
    def test_fix_144_contract(self) -> None:
        assert GOVERNANCE_SIMULATION_FIX == "FIX 144"
        assert GOVERNANCE_SIMULATION_SCHEMA_VERSION == "mission_control_governance_simulation_v1"
        assert MUTATION_PERFORMED_FIX_144 is False
        assert LIVE_POLICY_MUTATION_ENABLED_FIX_144 is False
        assert AUTO_POLICY_UPDATE_ENABLED_FIX_144 is False
        assert AUTOMATIC_GOVERNANCE_TUNING_ENABLED_FIX_144 is False
        assert SIMULATION_EXECUTABLE is False

    def test_governance_simulation_hypothetical_only(self) -> None:
        _full_stack(SESSION)
        result = run_governance_simulation(session_id=SESSION)
        assert result.ok is True
        assert result.simulation["simulation_only"] is True
        assert result.simulation["live_policy_mutation_enabled"] is False

    def test_operator_api_includes_governance_simulation_route(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/governance-simulation" in paths
