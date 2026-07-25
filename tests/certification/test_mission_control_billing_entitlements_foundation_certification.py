# SPDX-License-Identifier: Apache-2.0
"""FIX 305 — billing & entitlements foundation certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_305_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_contract import (
    AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_305,
    AUTOMATIC_SUBSCRIPTION_CREATION_ENABLED_FIX_305,
    BILLING_AUTHORITY_FIX_305,
    BILLING_ENTITLEMENTS_FOUNDATION_FIX,
    BILLING_ENTITLEMENTS_FOUNDATION_INVARIANT,
    BILLING_ENTITLEMENTS_FOUNDATION_ROUTE_ID,
    BILLING_ENTITLEMENTS_FOUNDATION_SCHEMA_VERSION,
    PAYMENT_PROCESSING_ENABLED_FIX_305,
)
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_service import (
    build_billing_entitlements_foundation,
)
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_store import (
    clear_billing_entitlements_foundation_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.orgs.organizations import clear_orgs_for_tests

pytestmark = pytest.mark.certification

SESSION = "mc-bef-cert-305"


@pytest.fixture(autouse=True)
def _clean():
    clear_billing_entitlements_foundation_records_for_tests()
    clear_orgs_for_tests()
    yield
    clear_billing_entitlements_foundation_records_for_tests()
    clear_orgs_for_tests()


class TestMissionControlBillingEntitlementsFoundationCertification:
    def test_fix_305_contract(self) -> None:
        assert BILLING_ENTITLEMENTS_FOUNDATION_FIX == "FIX 305"
        assert BILLING_ENTITLEMENTS_FOUNDATION_SCHEMA_VERSION == (
            "mission_control_billing_entitlements_foundation_v1"
        )
        assert BILLING_AUTHORITY_FIX_305 is False
        assert AUTOMATIC_SUBSCRIPTION_CREATION_ENABLED_FIX_305 is False
        assert AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_305 is False
        assert PAYMENT_PROCESSING_ENABLED_FIX_305 is False

    def test_fix_305_entitlements_not_authority(self) -> None:
        result = build_billing_entitlements_foundation(session_id=SESSION)
        board = result.billing_entitlements_foundation
        assert set(board["fix_305_certification_requirements"]) == set(FIX_305_CERTIFICATION_REQUIREMENTS)
        assert board["billing_authority"] is False
        assert "entitlements" in BILLING_ENTITLEMENTS_FOUNDATION_INVARIANT

    def test_fix_305_sections_present(self) -> None:
        result = build_billing_entitlements_foundation(session_id=SESSION)
        sections = result.billing_entitlements_foundation["sections"]
        for key in (
            "plan_registry",
            "subscription_registry",
            "entitlement_registry",
            "usage_registry",
            "capability_entitlement_matrix",
            "channel_entitlement_matrix",
            "provider_entitlement_matrix",
            "usage_limit_report",
            "billing_readiness_report",
            "billing_dashboard",
        ):
            assert sections[key]

    def test_fix_305_certification_requirement_count(self) -> None:
        assert len(FIX_305_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_305_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_305_route_id(self) -> None:
        assert BILLING_ENTITLEMENTS_FOUNDATION_ROUTE_ID == "mission_control_billing_entitlements_foundation"

    def test_fix_305_compose_only(self) -> None:
        result = build_billing_entitlements_foundation(session_id=SESSION)
        sources = result.billing_entitlements_foundation["sources"]
        assert sources["composes_fix_300_tenant_context"] is True
        assert sources["payment_collection_performed"] is False
        assert sources["subscription_mutation_performed"] is False
        assert sources["automatic_plan_change_performed"] is False
