# SPDX-License-Identifier: Apache-2.0
"""FIX 311 — public product experience certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_311_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.public_product_experience.public_product_experience_contract import (
    AUTOMATIC_CUSTOMER_ONBOARDING_ENABLED_FIX_311,
    PROVIDER_MUTATION_AUTHORITY_FIX_311,
    PUBLIC_PRODUCT_AUTHORITY_FIX_311,
    PUBLIC_PRODUCT_EXPERIENCE_FIX,
    PUBLIC_PRODUCT_EXPERIENCE_INVARIANT,
    PUBLIC_PRODUCT_EXPERIENCE_ROUTE_ID,
    PUBLIC_PRODUCT_EXPERIENCE_SCHEMA_VERSION,
    TENANT_MUTATION_AUTHORITY_FIX_311,
    TRUST_MUTATION_AUTHORITY_FIX_311,
)
from aethos_core.mission_control.public_product_experience.public_product_experience_service import (
    build_public_product_experience,
)
from aethos_core.mission_control.public_product_experience.public_product_experience_store import (
    clear_public_product_experience_records_for_tests,
)
from aethos_core.orgs.organizations import clear_orgs_for_tests

pytestmark = pytest.mark.certification

SESSION = "mc-ppe-cert-311"


@pytest.fixture(autouse=True)
def _clean():
    clear_public_product_experience_records_for_tests()
    clear_orgs_for_tests()
    yield
    clear_public_product_experience_records_for_tests()
    clear_orgs_for_tests()


class TestMissionControlPublicProductExperienceCertification:
    def test_fix_311_contract(self) -> None:
        assert PUBLIC_PRODUCT_EXPERIENCE_FIX == "FIX 311"
        assert PUBLIC_PRODUCT_EXPERIENCE_SCHEMA_VERSION == "mission_control_public_product_experience_v1"
        assert PUBLIC_PRODUCT_AUTHORITY_FIX_311 is False
        assert AUTOMATIC_CUSTOMER_ONBOARDING_ENABLED_FIX_311 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_311 is False
        assert PROVIDER_MUTATION_AUTHORITY_FIX_311 is False
        assert TENANT_MUTATION_AUTHORITY_FIX_311 is False

    def test_fix_311_experience_not_authority(self) -> None:
        result = build_public_product_experience(session_id=SESSION)
        board = result.public_product_experience
        assert set(board["fix_311_certification_requirements"]) == set(FIX_311_CERTIFICATION_REQUIREMENTS)
        assert board["public_product_authority"] is False
        assert "experience" in PUBLIC_PRODUCT_EXPERIENCE_INVARIANT

    def test_fix_311_sections_present(self) -> None:
        result = build_public_product_experience(session_id=SESSION)
        sections = result.public_product_experience["sections"]
        for key in (
            "public_landing_experience",
            "capability_explorer",
            "trust_explorer",
            "guided_product_tour",
            "use_case_explorer",
            "customer_journey_explorer",
            "plan_entitlement_explorer",
            "public_readiness_explorer",
            "public_education_center",
            "public_product_dashboard",
        ):
            assert sections[key]

    def test_fix_311_certification_requirement_count(self) -> None:
        assert len(FIX_311_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_311_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_311_route_id(self) -> None:
        assert PUBLIC_PRODUCT_EXPERIENCE_ROUTE_ID == "mission_control_public_product_experience"

    def test_fix_311_compose_only(self) -> None:
        result = build_public_product_experience(session_id=SESSION)
        sources = result.public_product_experience["sources"]
        assert sources["composes_fix_295_through_310"] is True
        assert sources["provider_execution_performed"] is False
        assert sources["governance_bypass_performed"] is False
        assert sources["tenant_mutation_performed"] is False
        assert sources["customer_provisioning_performed"] is False
        assert sources["automatic_onboarding_performed"] is False
