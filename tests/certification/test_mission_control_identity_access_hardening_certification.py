# SPDX-License-Identifier: Apache-2.0
"""FIX 302 — identity and access hardening certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_302_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_contract import (
    AUTHORIZATION_AUTHORITY_FIX_302,
    AUTHORIZATION_BYPASS_ENABLED_FIX_302,
    AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_302,
    AUTOMATIC_ROLE_ESCALATION_ENABLED_FIX_302,
    CROSS_TENANT_ACCESS_ENABLED_FIX_302,
    IDENTITY_ACCESS_HARDENING_FIX,
    IDENTITY_ACCESS_HARDENING_INVARIANT,
    IDENTITY_ACCESS_HARDENING_ROUTE_ID,
    IDENTITY_ACCESS_HARDENING_SCHEMA_VERSION,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_evaluator import (
    role_has_tenant_permission,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_service import (
    build_identity_access_hardening,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_store import (
    clear_identity_access_hardening_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.orgs.organizations import clear_orgs_for_tests

pytestmark = pytest.mark.certification

SESSION = "mc-iah-cert-302"


@pytest.fixture(autouse=True)
def _clean():
    clear_identity_access_hardening_records_for_tests()
    clear_orgs_for_tests()
    yield
    clear_identity_access_hardening_records_for_tests()
    clear_orgs_for_tests()


class TestMissionControlIdentityAccessHardeningCertification:
    def test_fix_302_contract(self) -> None:
        assert IDENTITY_ACCESS_HARDENING_FIX == "FIX 302"
        assert IDENTITY_ACCESS_HARDENING_SCHEMA_VERSION == (
            "mission_control_identity_access_hardening_v1"
        )
        assert AUTHORIZATION_AUTHORITY_FIX_302 is False
        assert AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_302 is False
        assert AUTOMATIC_ROLE_ESCALATION_ENABLED_FIX_302 is False
        assert CROSS_TENANT_ACCESS_ENABLED_FIX_302 is False
        assert AUTHORIZATION_BYPASS_ENABLED_FIX_302 is False

    def test_fix_302_enforcement_not_escalation(self) -> None:
        result = build_identity_access_hardening(session_id=SESSION)
        board = result.identity_access_hardening
        assert set(board["fix_302_certification_requirements"]) == set(FIX_302_CERTIFICATION_REQUIREMENTS)
        assert board["authorization_authority"] is False
        assert "authority_escalation" in IDENTITY_ACCESS_HARDENING_INVARIANT

    def test_fix_302_sections_present(self) -> None:
        result = build_identity_access_hardening(session_id=SESSION)
        sections = result.identity_access_hardening["sections"]
        for key in (
            "authorization_dashboard",
            "identity_resolution_report",
            "permission_evaluation_report",
            "tenant_boundary_audit",
            "mission_control_authorization_report",
            "repository_access_report",
            "governance_action_report",
            "authorization_audit_registry",
            "least_privilege_report",
            "channel_authorization_report",
            "session_trust_report",
        ):
            assert sections[key]

    def test_fix_302_certification_requirement_count(self) -> None:
        assert len(FIX_302_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_302_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_302_route_id(self) -> None:
        assert IDENTITY_ACCESS_HARDENING_ROUTE_ID == "mission_control_identity_access_hardening"

    def test_fix_302_regression_role_matrix(self) -> None:
        assert role_has_tenant_permission(role="viewer", permission="approve") is False
        assert role_has_tenant_permission(role="reviewer", permission="administer") is False
        assert role_has_tenant_permission(role="operator", permission="govern") is False

    def test_fix_302_compose_only(self) -> None:
        result = build_identity_access_hardening(session_id=SESSION)
        sources = result.identity_access_hardening["sources"]
        assert sources["composes_fix_300_multi_tenant_platform_foundation"] is True
        assert sources["composes_fix_301_tenant_onboarding_activation"] is True
        assert sources["permission_self_granting_performed"] is False
        assert sources["authorization_bypass_performed"] is False
