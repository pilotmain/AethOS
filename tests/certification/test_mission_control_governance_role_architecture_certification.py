# SPDX-License-Identifier: Apache-2.0
"""FIX 150 — governance role architecture certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.governance_role_architecture.governance_role_architecture_contract import (
    AUTOMATIC_APPROVAL_ENABLED_FIX_150,
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_150,
    AUTONOMOUS_ROLE_ELEVATION_ENABLED_FIX_150,
    DELEGATED_EXECUTION_AUTHORITY_ENABLED_FIX_150,
    GOVERNANCE_MUTATION_PERFORMED_FIX_150,
    GOVERNANCE_ROLE_ARCHITECTURE_FIX,
    GOVERNANCE_ROLE_ARCHITECTURE_SCHEMA_VERSION,
    GOVERNANCE_ROLE_TAXONOMY,
    MUTATION_PERFORMED_FIX_150,
    SEPARATION_OF_DUTY_POLICIES,
    TRUST_ZONES,
)
from aethos_core.mission_control.governance_role_architecture.governance_role_architecture_service import (
    build_governance_role_architecture,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-role-arch-cert-150"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()


class TestMissionControlGovernanceRoleArchitectureCertification:
    def test_fix_150_contract(self) -> None:
        assert GOVERNANCE_ROLE_ARCHITECTURE_FIX == "FIX 150"
        assert GOVERNANCE_ROLE_ARCHITECTURE_SCHEMA_VERSION == "mission_control_governance_role_architecture_v1"
        assert MUTATION_PERFORMED_FIX_150 is False
        assert DELEGATED_EXECUTION_AUTHORITY_ENABLED_FIX_150 is False
        assert AUTOMATIC_APPROVAL_ENABLED_FIX_150 is False
        assert AUTONOMOUS_ROLE_ELEVATION_ENABLED_FIX_150 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_150 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_150 is False
        assert "primary_reviewer" in GOVERNANCE_ROLE_TAXONOMY
        assert len(TRUST_ZONES) >= 6
        assert len(SEPARATION_OF_DUTY_POLICIES) >= 5

    def test_governance_role_architecture_institutional_topology(self) -> None:
        _full_stack(SESSION)
        result = build_governance_role_architecture(session_id=SESSION)
        assert result.ok is True
        assert result.architecture["institutional_governance_topology"] is True
        assert result.architecture["sections"]["quorum_role_composition_rules"]["automatic_quorum_approval"] is False

    def test_operator_api_includes_governance_role_architecture_route(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/governance-role-architecture" in paths
