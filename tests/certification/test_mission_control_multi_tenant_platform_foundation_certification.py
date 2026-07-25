# SPDX-License-Identifier: Apache-2.0
"""FIX 300 — multi-tenant platform foundation certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_300_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_contract import (
    AUTOMATIC_TENANT_CREATION_ENABLED_FIX_300,
    CROSS_TENANT_ACCESS_ENABLED_FIX_300,
    CROSS_TENANT_TRUST_ENABLED_FIX_300,
    MULTI_TENANT_PLATFORM_FOUNDATION_FIX,
    MULTI_TENANT_PLATFORM_FOUNDATION_INVARIANT,
    MULTI_TENANT_PLATFORM_FOUNDATION_PRINCIPLES,
    MULTI_TENANT_PLATFORM_FOUNDATION_ROUTE_ID,
    MULTI_TENANT_PLATFORM_FOUNDATION_SCHEMA_VERSION,
    PERMISSION_ESCALATION_ENABLED_FIX_300,
    TENANT_AUTHORITY_FIX_300,
)
from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_service import (
    build_multi_tenant_platform_foundation,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.orgs.organizations import clear_orgs_for_tests

pytestmark = pytest.mark.certification

SESSION = "mc-mtpf-cert-300"


@pytest.fixture(autouse=True)
def _clean_orgs():
    clear_orgs_for_tests()
    yield
    clear_orgs_for_tests()


class TestMissionControlMultiTenantPlatformFoundationCertification:
    def test_fix_300_contract(self) -> None:
        assert MULTI_TENANT_PLATFORM_FOUNDATION_FIX == "FIX 300"
        assert MULTI_TENANT_PLATFORM_FOUNDATION_SCHEMA_VERSION == (
            "mission_control_multi_tenant_platform_foundation_v1"
        )
        assert TENANT_AUTHORITY_FIX_300 is False
        assert AUTOMATIC_TENANT_CREATION_ENABLED_FIX_300 is False
        assert CROSS_TENANT_ACCESS_ENABLED_FIX_300 is False
        assert CROSS_TENANT_TRUST_ENABLED_FIX_300 is False
        assert PERMISSION_ESCALATION_ENABLED_FIX_300 is False

    def test_fix_300_tenancy_not_bypass(self) -> None:
        result = build_multi_tenant_platform_foundation(session_id=SESSION)
        board = result.multi_tenant_platform_foundation
        assert set(board["fix_300_certification_requirements"]) == set(FIX_300_CERTIFICATION_REQUIREMENTS)
        assert board["tenant_authority"] is False
        assert "governance_bypass" in MULTI_TENANT_PLATFORM_FOUNDATION_INVARIANT

    def test_fix_300_sections_present(self) -> None:
        result = build_multi_tenant_platform_foundation(session_id=SESSION)
        sections = result.multi_tenant_platform_foundation["sections"]
        assert sections["organization_registry"]
        assert sections["workspace_registry"]
        assert sections["project_registry"]
        assert sections["identity_registry"]
        assert sections["role_registry"]
        assert sections["permission_registry"]
        assert sections["tenant_trust_registry"]
        assert sections["tenant_governance_boundary_registry"]
        assert sections["tenant_onboarding_registry"]
        assert sections["channel_registry"]
        assert sections["tenant_dashboard"]
        assert len(MULTI_TENANT_PLATFORM_FOUNDATION_PRINCIPLES) >= 10

    def test_fix_300_certification_requirement_count(self) -> None:
        assert len(FIX_300_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_300_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_300_route_id(self) -> None:
        assert MULTI_TENANT_PLATFORM_FOUNDATION_ROUTE_ID == "mission_control_multi_tenant_platform_foundation"

    def test_fix_300_compose_only(self) -> None:
        result = build_multi_tenant_platform_foundation(session_id=SESSION)
        sources = result.multi_tenant_platform_foundation["sources"]
        assert sources["pilot_reexecution_performed"] is False
        assert sources["automatic_tenant_provisioning_performed"] is False
        assert sources["cross_tenant_access_performed"] is False
