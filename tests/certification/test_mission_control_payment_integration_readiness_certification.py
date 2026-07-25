# SPDX-License-Identifier: Apache-2.0
"""FIX 308 — payment integration readiness certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_308_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_contract import (
    AUTOMATIC_CHARGING_ENABLED_FIX_308,
    AUTOMATIC_REFUND_ENABLED_FIX_308,
    CREDIT_CARD_STORAGE_ENABLED_FIX_308,
    PAYMENT_INTEGRATION_READINESS_FIX,
    PAYMENT_INTEGRATION_READINESS_INVARIANT,
    PAYMENT_INTEGRATION_READINESS_ROUTE_ID,
    PAYMENT_INTEGRATION_READINESS_SCHEMA_VERSION,
    PAYMENT_PROCESSING_ENABLED_FIX_308,
    SUBSCRIPTION_MUTATION_AUTHORITY_FIX_308,
)
from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_service import (
    build_payment_integration_readiness,
)
from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_store import (
    clear_payment_integration_readiness_records_for_tests,
)
from aethos_core.orgs.organizations import clear_orgs_for_tests

pytestmark = pytest.mark.certification

SESSION = "mc-pir-cert-308"


@pytest.fixture(autouse=True)
def _clean():
    clear_payment_integration_readiness_records_for_tests()
    clear_orgs_for_tests()
    yield
    clear_payment_integration_readiness_records_for_tests()
    clear_orgs_for_tests()


class TestMissionControlPaymentIntegrationReadinessCertification:
    def test_fix_308_contract(self) -> None:
        assert PAYMENT_INTEGRATION_READINESS_FIX == "FIX 308"
        assert PAYMENT_INTEGRATION_READINESS_SCHEMA_VERSION == (
            "mission_control_payment_integration_readiness_v1"
        )
        assert PAYMENT_PROCESSING_ENABLED_FIX_308 is False
        assert CREDIT_CARD_STORAGE_ENABLED_FIX_308 is False
        assert AUTOMATIC_CHARGING_ENABLED_FIX_308 is False
        assert AUTOMATIC_REFUND_ENABLED_FIX_308 is False
        assert SUBSCRIPTION_MUTATION_AUTHORITY_FIX_308 is False

    def test_fix_308_readiness_not_processing(self) -> None:
        result = build_payment_integration_readiness(session_id=SESSION)
        board = result.payment_integration_readiness
        assert set(board["fix_308_certification_requirements"]) == set(FIX_308_CERTIFICATION_REQUIREMENTS)
        assert board["payment_processing_enabled"] is False
        assert "readiness" in PAYMENT_INTEGRATION_READINESS_INVARIANT

    def test_fix_308_sections_present(self) -> None:
        result = build_payment_integration_readiness(session_id=SESSION)
        sections = result.payment_integration_readiness["sections"]
        for key in (
            "customer_billing_identity_registry",
            "payment_provider_registry",
            "subscription_lifecycle_registry",
            "billing_event_registry",
            "invoice_readiness_registry",
            "usage_monetization_registry",
            "commercial_analytics_dashboard",
            "upgrade_path_registry",
            "payment_readiness_dashboard",
            "commercial_governance_report",
        ):
            assert sections[key]

    def test_fix_308_certification_requirement_count(self) -> None:
        assert len(FIX_308_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_308_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_308_route_id(self) -> None:
        assert PAYMENT_INTEGRATION_READINESS_ROUTE_ID == "mission_control_payment_integration_readiness"

    def test_fix_308_compose_only(self) -> None:
        result = build_payment_integration_readiness(session_id=SESSION)
        sources = result.payment_integration_readiness["sources"]
        assert sources["composes_fix_305_billing_entitlements"] is True
        assert sources["payment_collection_performed"] is False
        assert sources["subscription_mutation_performed"] is False
        assert sources["provider_api_mutation_performed"] is False
