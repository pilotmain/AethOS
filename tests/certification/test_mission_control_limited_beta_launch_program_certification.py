# SPDX-License-Identifier: Apache-2.0
"""FIX 312 — limited beta launch program certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_312_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_contract import (
    AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_312,
    AUTOMATIC_CUSTOMER_PROVISIONING_ENABLED_FIX_312,
    AUTOMATIC_PLAN_ASSIGNMENT_ENABLED_FIX_312,
    AUTOMATIC_USER_ADMISSION_ENABLED_FIX_312,
    BETA_AUTHORITY_FIX_312,
    LIMITED_BETA_LAUNCH_PROGRAM_FIX,
    LIMITED_BETA_LAUNCH_PROGRAM_INVARIANT,
    LIMITED_BETA_LAUNCH_PROGRAM_ROUTE_ID,
    LIMITED_BETA_LAUNCH_PROGRAM_SCHEMA_VERSION,
)
from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_service import (
    build_limited_beta_launch_program,
)
from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_store import (
    clear_limited_beta_launch_program_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.orgs.organizations import clear_orgs_for_tests

pytestmark = pytest.mark.certification

SESSION = "mc-lblp-cert-312"


@pytest.fixture(autouse=True)
def _clean():
    clear_limited_beta_launch_program_records_for_tests()
    clear_orgs_for_tests()
    yield
    clear_limited_beta_launch_program_records_for_tests()
    clear_orgs_for_tests()


class TestMissionControlLimitedBetaLaunchProgramCertification:
    def test_fix_312_contract(self) -> None:
        assert LIMITED_BETA_LAUNCH_PROGRAM_FIX == "FIX 312"
        assert LIMITED_BETA_LAUNCH_PROGRAM_SCHEMA_VERSION == "mission_control_limited_beta_launch_program_v1"
        assert BETA_AUTHORITY_FIX_312 is False
        assert AUTOMATIC_USER_ADMISSION_ENABLED_FIX_312 is False
        assert AUTOMATIC_CUSTOMER_PROVISIONING_ENABLED_FIX_312 is False
        assert AUTOMATIC_PLAN_ASSIGNMENT_ENABLED_FIX_312 is False
        assert AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_312 is False

    def test_fix_312_management_not_provisioning(self) -> None:
        result = build_limited_beta_launch_program(session_id=SESSION)
        board = result.limited_beta_launch_program
        assert set(board["fix_312_certification_requirements"]) == set(FIX_312_CERTIFICATION_REQUIREMENTS)
        assert board["beta_authority"] is False
        assert "provisioning" in LIMITED_BETA_LAUNCH_PROGRAM_INVARIANT

    def test_fix_312_sections_present(self) -> None:
        result = build_limited_beta_launch_program(session_id=SESSION)
        sections = result.limited_beta_launch_program["sections"]
        for key in (
            "beta_cohort_registry",
            "beta_candidate_registry",
            "beta_admission_review_registry",
            "beta_readiness_report",
            "beta_feedback_registry",
            "beta_risk_registry",
            "beta_success_metrics",
            "beta_operations_dashboard",
            "beta_evidence_registry",
            "beta_launch_recommendation",
        ):
            assert sections[key]

    def test_fix_312_certification_requirement_count(self) -> None:
        assert len(FIX_312_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_312_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_312_route_id(self) -> None:
        assert LIMITED_BETA_LAUNCH_PROGRAM_ROUTE_ID == "mission_control_limited_beta_launch_program"

    def test_fix_312_compose_only(self) -> None:
        result = build_limited_beta_launch_program(session_id=SESSION)
        sources = result.limited_beta_launch_program["sources"]
        assert sources["composes_fix_300_through_311"] is True
        assert sources["user_provisioning_performed"] is False
        assert sources["entitlement_mutation_performed"] is False
        assert sources["automatic_launch_performed"] is False
        assert sources["automatic_beta_expansion_performed"] is False
