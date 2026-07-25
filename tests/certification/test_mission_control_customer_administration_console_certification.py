# SPDX-License-Identifier: Apache-2.0
"""FIX 306 — customer administration console certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_306_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.customer_administration_console.customer_administration_console_contract import (
    ADMINISTRATION_AUTHORITY_FIX_306,
    AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_306,
    AUTOMATIC_USER_CREATION_ENABLED_FIX_306,
    BILLING_MUTATION_AUTHORITY_FIX_306,
    CROSS_TENANT_ADMINISTRATION_ENABLED_FIX_306,
    CUSTOMER_ADMINISTRATION_CONSOLE_FIX,
    CUSTOMER_ADMINISTRATION_CONSOLE_INVARIANT,
    CUSTOMER_ADMINISTRATION_CONSOLE_ROUTE_ID,
    CUSTOMER_ADMINISTRATION_CONSOLE_SCHEMA_VERSION,
    TRUST_MUTATION_AUTHORITY_FIX_306,
)
from aethos_core.mission_control.customer_administration_console.customer_administration_console_service import (
    build_customer_administration_console,
)
from aethos_core.mission_control.customer_administration_console.customer_administration_console_store import (
    clear_customer_administration_console_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.orgs.organizations import clear_orgs_for_tests

pytestmark = pytest.mark.certification

SESSION = "mc-cac-cert-306"


@pytest.fixture(autouse=True)
def _clean():
    clear_customer_administration_console_records_for_tests()
    clear_orgs_for_tests()
    yield
    clear_customer_administration_console_records_for_tests()
    clear_orgs_for_tests()


class TestMissionControlCustomerAdministrationConsoleCertification:
    def test_fix_306_contract(self) -> None:
        assert CUSTOMER_ADMINISTRATION_CONSOLE_FIX == "FIX 306"
        assert CUSTOMER_ADMINISTRATION_CONSOLE_SCHEMA_VERSION == (
            "mission_control_customer_administration_console_v1"
        )
        assert ADMINISTRATION_AUTHORITY_FIX_306 is False
        assert AUTOMATIC_USER_CREATION_ENABLED_FIX_306 is False
        assert AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_306 is False
        assert CROSS_TENANT_ADMINISTRATION_ENABLED_FIX_306 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_306 is False
        assert BILLING_MUTATION_AUTHORITY_FIX_306 is False

    def test_fix_306_visibility_not_authority(self) -> None:
        result = build_customer_administration_console(session_id=SESSION)
        board = result.customer_administration_console
        assert set(board["fix_306_certification_requirements"]) == set(FIX_306_CERTIFICATION_REQUIREMENTS)
        assert board["administration_authority"] is False
        assert "visibility" in CUSTOMER_ADMINISTRATION_CONSOLE_INVARIANT

    def test_fix_306_sections_present(self) -> None:
        result = build_customer_administration_console(session_id=SESSION)
        sections = result.customer_administration_console["sections"]
        for key in (
            "organization_administration_report",
            "user_administration_report",
            "role_administration_report",
            "workspace_administration_report",
            "project_administration_report",
            "provider_administration_report",
            "channel_administration_report",
            "billing_administration_report",
            "governance_administration_report",
            "customer_administration_dashboard",
        ):
            assert sections[key]

    def test_fix_306_certification_requirement_count(self) -> None:
        assert len(FIX_306_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_306_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_306_route_id(self) -> None:
        assert CUSTOMER_ADMINISTRATION_CONSOLE_ROUTE_ID == "mission_control_customer_administration_console"

    def test_fix_306_compose_only(self) -> None:
        result = build_customer_administration_console(session_id=SESSION)
        sources = result.customer_administration_console["sources"]
        assert sources["composes_fix_300_tenant_context"] is True
        assert sources["composes_fix_305_billing_context"] is True
        assert sources["automatic_user_creation_performed"] is False
        assert sources["cross_tenant_administration_performed"] is False
