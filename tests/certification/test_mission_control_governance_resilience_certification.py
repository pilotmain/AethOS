# SPDX-License-Identifier: Apache-2.0
"""FIX 154 — governance resilience certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.governance_resilience.governance_resilience_contract import (
    AUTOMATIC_GOVERNANCE_ADAPTATION_ENABLED_FIX_154,
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_154,
    AUTONOMOUS_RESILIENCE_CORRECTION_ENABLED_FIX_154,
    GOVERNANCE_MUTATION_PERFORMED_FIX_154,
    GOVERNANCE_RESILIENCE_FIX,
    GOVERNANCE_RESILIENCE_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_154,
    OVERRIDE_AUTHORITY_ENABLED_FIX_154,
    RESILIENCE_COGNITION_PRINCIPLES,
    RESILIENCE_RECORD_KINDS,
    RESILIENCE_SIMULATION_EXECUTABLE,
    SELF_HEALING_GOVERNANCE_ENABLED_FIX_154,
    STRESS_SCENARIO_CATALOG,
)
from aethos_core.mission_control.governance_resilience.governance_resilience_service import build_governance_resilience
from aethos_core.mission_control.governance_resilience.governance_resilience_store import (
    append_governance_resilience_record,
    clear_governance_resilience_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-resilience-cert-154"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_governance_resilience_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_governance_resilience_records_for_tests()


class TestMissionControlGovernanceResilienceCertification:
    def test_fix_154_contract(self) -> None:
        assert GOVERNANCE_RESILIENCE_FIX == "FIX 154"
        assert GOVERNANCE_RESILIENCE_SCHEMA_VERSION == "mission_control_governance_resilience_v1"
        assert MUTATION_PERFORMED_FIX_154 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_154 is False
        assert AUTOMATIC_GOVERNANCE_ADAPTATION_ENABLED_FIX_154 is False
        assert AUTONOMOUS_RESILIENCE_CORRECTION_ENABLED_FIX_154 is False
        assert SELF_HEALING_GOVERNANCE_ENABLED_FIX_154 is False
        assert OVERRIDE_AUTHORITY_ENABLED_FIX_154 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_154 is False
        assert RESILIENCE_SIMULATION_EXECUTABLE is False
        assert "stress_scenario" in RESILIENCE_RECORD_KINDS
        assert len(RESILIENCE_COGNITION_PRINCIPLES) >= 8
        assert len(STRESS_SCENARIO_CATALOG) >= 8

    def test_governance_resilience_cognition_layer(self) -> None:
        _full_stack(SESSION)
        record, blockers = append_governance_resilience_record(
            session_id=SESSION,
            kind="resilience_observation",
            content="Advisory: simulated approval-chain overload under concurrent gate pressure.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False
        assert record["simulation_only"] is True

        result = build_governance_resilience(session_id=SESSION)
        assert result.ok is True
        assert result.resilience["institutional_resilience_cognition"] is True
        assert result.resilience["resilience_record_count"] == 1

    def test_operator_api_includes_governance_resilience_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/governance-resilience" in paths
        assert "/mission-control/governance-resilience/record" in paths
