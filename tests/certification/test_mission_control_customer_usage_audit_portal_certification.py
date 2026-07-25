# SPDX-License-Identifier: Apache-2.0
"""FIX 307 — customer usage & audit portal certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_307_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_contract import (
    AUDIT_AUTHORITY_FIX_307,
    AUDIT_MUTATION_ENABLED_FIX_307,
    AUTHORIZATION_BYPASS_ENABLED_FIX_307,
    CROSS_TENANT_AUDIT_ACCESS_ENABLED_FIX_307,
    CUSTOMER_USAGE_AUDIT_PORTAL_FIX,
    CUSTOMER_USAGE_AUDIT_PORTAL_INVARIANT,
    CUSTOMER_USAGE_AUDIT_PORTAL_ROUTE_ID,
    CUSTOMER_USAGE_AUDIT_PORTAL_SCHEMA_VERSION,
    EVIDENCE_MUTATION_ENABLED_FIX_307,
)
from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_service import (
    build_customer_usage_audit_portal,
)
from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_store import (
    clear_customer_usage_audit_portal_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.orgs.organizations import clear_orgs_for_tests

pytestmark = pytest.mark.certification

SESSION = "mc-cuap-cert-307"


@pytest.fixture(autouse=True)
def _clean():
    clear_customer_usage_audit_portal_records_for_tests()
    clear_orgs_for_tests()
    yield
    clear_customer_usage_audit_portal_records_for_tests()
    clear_orgs_for_tests()


class TestMissionControlCustomerUsageAuditPortalCertification:
    def test_fix_307_contract(self) -> None:
        assert CUSTOMER_USAGE_AUDIT_PORTAL_FIX == "FIX 307"
        assert CUSTOMER_USAGE_AUDIT_PORTAL_SCHEMA_VERSION == (
            "mission_control_customer_usage_audit_portal_v1"
        )
        assert AUDIT_AUTHORITY_FIX_307 is False
        assert AUDIT_MUTATION_ENABLED_FIX_307 is False
        assert EVIDENCE_MUTATION_ENABLED_FIX_307 is False
        assert CROSS_TENANT_AUDIT_ACCESS_ENABLED_FIX_307 is False
        assert AUTHORIZATION_BYPASS_ENABLED_FIX_307 is False

    def test_fix_307_visibility_not_authority(self) -> None:
        result = build_customer_usage_audit_portal(session_id=SESSION)
        board = result.customer_usage_audit_portal
        assert set(board["fix_307_certification_requirements"]) == set(FIX_307_CERTIFICATION_REQUIREMENTS)
        assert board["audit_authority"] is False
        assert "visibility" in CUSTOMER_USAGE_AUDIT_PORTAL_INVARIANT

    def test_fix_307_sections_present(self) -> None:
        result = build_customer_usage_audit_portal(session_id=SESSION)
        sections = result.customer_usage_audit_portal["sections"]
        for key in (
            "activity_timeline",
            "governance_timeline",
            "usage_timeline",
            "audit_registry",
            "repository_activity_report",
            "user_activity_report",
            "provider_activity_report",
            "billing_usage_history_report",
            "evidence_explorer",
            "customer_audit_dashboard",
        ):
            assert sections[key]

    def test_fix_307_certification_requirement_count(self) -> None:
        assert len(FIX_307_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_307_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_307_route_id(self) -> None:
        assert CUSTOMER_USAGE_AUDIT_PORTAL_ROUTE_ID == "mission_control_customer_usage_audit_portal"

    def test_fix_307_compose_only(self) -> None:
        result = build_customer_usage_audit_portal(session_id=SESSION)
        sources = result.customer_usage_audit_portal["sources"]
        assert sources["composes_fix_305_billing_history"] is True
        assert sources["audit_mutation_performed"] is False
        assert sources["evidence_mutation_performed"] is False
        assert sources["cross_tenant_audit_access_performed"] is False
