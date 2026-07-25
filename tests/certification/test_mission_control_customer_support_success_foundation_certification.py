# SPDX-License-Identifier: Apache-2.0
"""FIX 310 — customer support & success foundation certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_310_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_contract import (
    AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_310,
    AUTOMATIC_ESCALATION_ENABLED_FIX_310,
    AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_310,
    AUTOMATIC_SUPPORT_RESOLUTION_ENABLED_FIX_310,
    CUSTOMER_SUPPORT_AUTHORITY_FIX_310,
    CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_FIX,
    CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_INVARIANT,
    CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_ROUTE_ID,
    CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_SCHEMA_VERSION,
)
from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_service import (
    build_customer_support_success_foundation,
)
from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_store import (
    clear_customer_support_success_foundation_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.orgs.organizations import clear_orgs_for_tests

pytestmark = pytest.mark.certification

SESSION = "mc-cssf-cert-310"


@pytest.fixture(autouse=True)
def _clean():
    clear_customer_support_success_foundation_records_for_tests()
    clear_orgs_for_tests()
    yield
    clear_customer_support_success_foundation_records_for_tests()
    clear_orgs_for_tests()


class TestMissionControlCustomerSupportSuccessFoundationCertification:
    def test_fix_310_contract(self) -> None:
        assert CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_FIX == "FIX 310"
        assert CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_SCHEMA_VERSION == (
            "mission_control_customer_support_success_foundation_v1"
        )
        assert CUSTOMER_SUPPORT_AUTHORITY_FIX_310 is False
        assert AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_310 is False
        assert AUTOMATIC_ESCALATION_ENABLED_FIX_310 is False
        assert AUTOMATIC_SUPPORT_RESOLUTION_ENABLED_FIX_310 is False
        assert AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_310 is False

    def test_fix_310_visibility_not_authority(self) -> None:
        result = build_customer_support_success_foundation(session_id=SESSION)
        board = result.customer_support_success_foundation
        assert set(board["fix_310_certification_requirements"]) == set(FIX_310_CERTIFICATION_REQUIREMENTS)
        assert board["customer_support_authority"] is False
        assert "visibility" in CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_INVARIANT

    def test_fix_310_sections_present(self) -> None:
        result = build_customer_support_success_foundation(session_id=SESSION)
        sections = result.customer_support_success_foundation["sections"]
        for key in (
            "customer_health_registry",
            "customer_success_dashboard",
            "support_request_registry",
            "customer_adoption_report",
            "customer_trust_report",
            "customer_risk_registry",
            "customer_escalation_registry",
            "success_opportunity_registry",
            "support_analytics_dashboard",
            "customer_support_success_dashboard",
        ):
            assert sections[key]

    def test_fix_310_certification_requirement_count(self) -> None:
        assert len(FIX_310_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_310_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_310_route_id(self) -> None:
        assert CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_ROUTE_ID == (
            "mission_control_customer_support_success_foundation"
        )

    def test_fix_310_compose_only(self) -> None:
        result = build_customer_support_success_foundation(session_id=SESSION)
        sources = result.customer_support_success_foundation["sources"]
        assert sources["composes_fix_300_through_309"] is True
        assert sources["customer_contact_performed"] is False
        assert sources["ticket_execution_performed"] is False
        assert sources["provider_mutation_performed"] is False
        assert sources["subscription_mutation_performed"] is False
