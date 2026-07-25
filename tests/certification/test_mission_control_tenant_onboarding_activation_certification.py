# SPDX-License-Identifier: Apache-2.0
"""FIX 301 — tenant onboarding and activation certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_301_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_contract import (
    AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_301,
    AUTOMATIC_PROVISIONING_ENABLED_FIX_301,
    ONBOARDING_AUTHORITY_FIX_301,
    SECRET_COLLECTION_ENABLED_FIX_301,
    TENANT_ONBOARDING_ACTIVATION_FIX,
    TENANT_ONBOARDING_ACTIVATION_INVARIANT,
    TENANT_ONBOARDING_ACTIVATION_ROUTE_ID,
    TENANT_ONBOARDING_ACTIVATION_SCHEMA_VERSION,
    TRUST_MUTATION_AUTHORITY_FIX_301,
)
from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_service import (
    build_tenant_onboarding_activation,
)
from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_store import (
    clear_tenant_onboarding_activation_records_for_tests,
)
from aethos_core.orgs.organizations import clear_orgs_for_tests

pytestmark = pytest.mark.certification

SESSION = "mc-toa-cert-301"


@pytest.fixture(autouse=True)
def _clean():
    clear_tenant_onboarding_activation_records_for_tests()
    clear_orgs_for_tests()
    yield
    clear_tenant_onboarding_activation_records_for_tests()
    clear_orgs_for_tests()


class TestMissionControlTenantOnboardingActivationCertification:
    def test_fix_301_contract(self) -> None:
        assert TENANT_ONBOARDING_ACTIVATION_FIX == "FIX 301"
        assert TENANT_ONBOARDING_ACTIVATION_SCHEMA_VERSION == (
            "mission_control_tenant_onboarding_activation_v1"
        )
        assert ONBOARDING_AUTHORITY_FIX_301 is False
        assert AUTOMATIC_PROVISIONING_ENABLED_FIX_301 is False
        assert AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_301 is False
        assert SECRET_COLLECTION_ENABLED_FIX_301 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_301 is False

    def test_fix_301_onboarding_not_authority(self) -> None:
        result = build_tenant_onboarding_activation(session_id=SESSION)
        board = result.tenant_onboarding_activation
        assert set(board["fix_301_certification_requirements"]) == set(FIX_301_CERTIFICATION_REQUIREMENTS)
        assert board["onboarding_authority"] is False
        assert "platform_authority" in TENANT_ONBOARDING_ACTIVATION_INVARIANT

    def test_fix_301_sections_present(self) -> None:
        result = build_tenant_onboarding_activation(session_id=SESSION)
        sections = result.tenant_onboarding_activation["sections"]
        for key in (
            "tenant_onboarding_dashboard",
            "organization_setup_review",
            "workspace_setup_review",
            "project_registration_review",
            "provider_connection_checklist",
            "capability_discovery_report",
            "trust_explanation_report",
            "first_mission_control_activation_packet",
            "onboarding_progress_registry",
        ):
            assert sections[key]

    def test_fix_301_certification_requirement_count(self) -> None:
        assert len(FIX_301_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_301_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_301_route_id(self) -> None:
        assert TENANT_ONBOARDING_ACTIVATION_ROUTE_ID == "mission_control_tenant_onboarding_activation"

    def test_fix_301_compose_only(self) -> None:
        result = build_tenant_onboarding_activation(session_id=SESSION)
        sources = result.tenant_onboarding_activation["sources"]
        assert sources["composes_fix_300_multi_tenant_platform_foundation"] is True
        assert sources["composes_fix_295_capability_registry"] is True
        assert sources["composes_fix_296_runtime_capability_integration"] is True
        assert sources["automatic_provisioning_performed"] is False
        assert sources["secret_collection_performed"] is False
