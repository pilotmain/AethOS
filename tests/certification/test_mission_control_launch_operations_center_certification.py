# SPDX-License-Identifier: Apache-2.0
"""FIX 313 — launch operations center certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_313_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.launch_operations_center.launch_operations_center_contract import (
    AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_313,
    AUTOMATIC_CUSTOMER_ADMISSION_ENABLED_FIX_313,
    AUTOMATIC_LAUNCH_ENABLED_FIX_313,
    AUTOMATIC_PROVIDER_MUTATION_ENABLED_FIX_313,
    LAUNCH_OPERATIONS_AUTHORITY_FIX_313,
    LAUNCH_OPERATIONS_CENTER_FIX,
    LAUNCH_OPERATIONS_CENTER_INVARIANT,
    LAUNCH_OPERATIONS_CENTER_ROUTE_ID,
    LAUNCH_OPERATIONS_CENTER_SCHEMA_VERSION,
)
from aethos_core.mission_control.launch_operations_center.launch_operations_center_service import (
    build_launch_operations_center,
)
from aethos_core.mission_control.launch_operations_center.launch_operations_center_store import (
    clear_launch_operations_center_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.orgs.organizations import clear_orgs_for_tests

pytestmark = pytest.mark.certification

SESSION = "mc-loc-cert-313"


@pytest.fixture(autouse=True)
def _clean():
    clear_launch_operations_center_records_for_tests()
    clear_orgs_for_tests()
    yield
    clear_launch_operations_center_records_for_tests()
    clear_orgs_for_tests()


class TestMissionControlLaunchOperationsCenterCertification:
    def test_fix_313_contract(self) -> None:
        assert LAUNCH_OPERATIONS_CENTER_FIX == "FIX 313"
        assert LAUNCH_OPERATIONS_CENTER_SCHEMA_VERSION == "mission_control_launch_operations_center_v1"
        assert LAUNCH_OPERATIONS_AUTHORITY_FIX_313 is False
        assert AUTOMATIC_LAUNCH_ENABLED_FIX_313 is False
        assert AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_313 is False
        assert AUTOMATIC_CUSTOMER_ADMISSION_ENABLED_FIX_313 is False
        assert AUTOMATIC_PROVIDER_MUTATION_ENABLED_FIX_313 is False

    def test_fix_313_visibility_not_authority(self) -> None:
        result = build_launch_operations_center(session_id=SESSION)
        board = result.launch_operations_center
        assert set(board["fix_313_certification_requirements"]) == set(FIX_313_CERTIFICATION_REQUIREMENTS)
        assert board["launch_operations_authority"] is False
        assert "visibility" in LAUNCH_OPERATIONS_CENTER_INVARIANT

    def test_fix_313_sections_present(self) -> None:
        result = build_launch_operations_center(session_id=SESSION)
        sections = result.launch_operations_center["sections"]
        for key in (
            "launch_status_registry",
            "launch_blocker_registry",
            "launch_risk_dashboard",
            "beta_operations_monitor",
            "customer_operations_monitor",
            "platform_operations_monitor",
            "provider_operations_monitor",
            "launch_evidence_registry",
            "launch_recommendation",
            "launch_operations_dashboard",
        ):
            assert sections[key]

    def test_fix_313_certification_requirement_count(self) -> None:
        assert len(FIX_313_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_313_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_313_route_id(self) -> None:
        assert LAUNCH_OPERATIONS_CENTER_ROUTE_ID == "mission_control_launch_operations_center"

    def test_fix_313_compose_only(self) -> None:
        result = build_launch_operations_center(session_id=SESSION)
        sources = result.launch_operations_center["sources"]
        assert sources["composes_fix_309_through_312_and_lifecycle"] is True
        assert sources["launch_execution_performed"] is False
        assert sources["customer_provisioning_performed"] is False
        assert sources["beta_expansion_performed"] is False
        assert sources["provider_mutation_performed"] is False
