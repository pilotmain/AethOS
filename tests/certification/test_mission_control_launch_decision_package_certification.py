# SPDX-License-Identifier: Apache-2.0
"""FIX 315 — launch decision package certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_315_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.launch_decision_package.launch_decision_package_contract import (
    AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_315,
    AUTOMATIC_LAUNCH_APPROVAL_ENABLED_FIX_315,
    AUTOMATIC_LAUNCH_ENABLED_FIX_315,
    LAUNCH_DECISION_AUTHORITY_FIX_315,
    LAUNCH_DECISION_PACKAGE_DOMAINS,
    LAUNCH_DECISION_PACKAGE_FIX,
    LAUNCH_DECISION_PACKAGE_INVARIANT,
    LAUNCH_DECISION_PACKAGE_ROUTE_ID,
    LAUNCH_DECISION_PACKAGE_SCHEMA_VERSION,
    TRUST_MUTATION_AUTHORITY_FIX_315,
)
from aethos_core.mission_control.launch_decision_package.launch_decision_package_service import (
    build_launch_decision_package,
)
from aethos_core.mission_control.launch_decision_package.launch_decision_package_store import (
    clear_launch_decision_package_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_store import (
    clear_public_launch_readiness_freeze_records_for_tests,
)
from aethos_core.orgs.organizations import clear_orgs_for_tests

pytestmark = pytest.mark.certification

SESSION = "mc-ldp-cert-315"


@pytest.fixture(autouse=True)
def _clean():
    clear_launch_decision_package_records_for_tests()
    clear_public_launch_readiness_freeze_records_for_tests()
    clear_orgs_for_tests()
    yield
    clear_launch_decision_package_records_for_tests()
    clear_public_launch_readiness_freeze_records_for_tests()
    clear_orgs_for_tests()


class TestMissionControlLaunchDecisionPackageCertification:
    def test_fix_315_contract(self) -> None:
        assert LAUNCH_DECISION_PACKAGE_FIX == "FIX 315"
        assert LAUNCH_DECISION_PACKAGE_SCHEMA_VERSION == "mission_control_launch_decision_package_v1"
        assert LAUNCH_DECISION_AUTHORITY_FIX_315 is False
        assert AUTOMATIC_LAUNCH_APPROVAL_ENABLED_FIX_315 is False
        assert AUTOMATIC_LAUNCH_ENABLED_FIX_315 is False
        assert AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_315 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_315 is False

    def test_fix_315_package_not_decision(self) -> None:
        result = build_launch_decision_package(session_id=SESSION)
        board = result.launch_decision_package
        assert set(board["fix_315_certification_requirements"]) == set(FIX_315_CERTIFICATION_REQUIREMENTS)
        assert board["launch_decision_authority"] is False
        assert "authority" in LAUNCH_DECISION_PACKAGE_INVARIANT

    def test_fix_315_domains_present(self) -> None:
        result = build_launch_decision_package(session_id=SESSION)
        sections = result.launch_decision_package["sections"]
        for key in LAUNCH_DECISION_PACKAGE_DOMAINS:
            assert sections[key]

    def test_fix_315_certification_requirement_count(self) -> None:
        assert len(FIX_315_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_315_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_315_route_id(self) -> None:
        assert LAUNCH_DECISION_PACKAGE_ROUTE_ID == "mission_control_launch_decision_package"

    def test_fix_315_compose_only(self) -> None:
        result = build_launch_decision_package(session_id=SESSION)
        sources = result.launch_decision_package["sources"]
        assert sources["composes_fix_186_through_314"] is True
        assert sources["pilot_execution_performed"] is False
        assert sources["launch_approval_performed"] is False
        assert sources["launch_execution_performed"] is False
        assert sources["trust_mutation_performed"] is False
        assert sources["customer_provisioning_performed"] is False
        assert sources["beta_expansion_performed"] is False
