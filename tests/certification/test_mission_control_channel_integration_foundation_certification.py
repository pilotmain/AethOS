# SPDX-License-Identifier: Apache-2.0
"""FIX 304 — channel integration foundation certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_304_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_contract import (
    AUTHORIZATION_BYPASS_ENABLED_FIX_304,
    AUTOMATIC_CHANNEL_PROVISIONING_ENABLED_FIX_304,
    CHANNEL_AUTHORITY_FIX_304,
    CHANNEL_INTEGRATION_FOUNDATION_FIX,
    CHANNEL_INTEGRATION_FOUNDATION_INVARIANT,
    CHANNEL_INTEGRATION_FOUNDATION_ROUTE_ID,
    CHANNEL_INTEGRATION_FOUNDATION_SCHEMA_VERSION,
    CROSS_CHANNEL_IDENTITY_BYPASS_ENABLED_FIX_304,
    CROSS_TENANT_CHANNEL_ACCESS_ENABLED_FIX_304,
)
from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_service import (
    build_channel_integration_foundation,
)
from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_store import (
    clear_channel_integration_foundation_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.orgs.organizations import clear_orgs_for_tests

pytestmark = pytest.mark.certification

SESSION = "mc-cif-cert-304"


@pytest.fixture(autouse=True)
def _clean():
    clear_channel_integration_foundation_records_for_tests()
    clear_orgs_for_tests()
    yield
    clear_channel_integration_foundation_records_for_tests()
    clear_orgs_for_tests()


class TestMissionControlChannelIntegrationFoundationCertification:
    def test_fix_304_contract(self) -> None:
        assert CHANNEL_INTEGRATION_FOUNDATION_FIX == "FIX 304"
        assert CHANNEL_INTEGRATION_FOUNDATION_SCHEMA_VERSION == (
            "mission_control_channel_integration_foundation_v1"
        )
        assert CHANNEL_AUTHORITY_FIX_304 is False
        assert AUTOMATIC_CHANNEL_PROVISIONING_ENABLED_FIX_304 is False
        assert CROSS_CHANNEL_IDENTITY_BYPASS_ENABLED_FIX_304 is False
        assert CROSS_TENANT_CHANNEL_ACCESS_ENABLED_FIX_304 is False
        assert AUTHORIZATION_BYPASS_ENABLED_FIX_304 is False

    def test_fix_304_integration_not_duplication(self) -> None:
        result = build_channel_integration_foundation(session_id=SESSION)
        board = result.channel_integration_foundation
        assert set(board["fix_304_certification_requirements"]) == set(FIX_304_CERTIFICATION_REQUIREMENTS)
        assert board["channel_authority"] is False
        assert "channel_specific" in CHANNEL_INTEGRATION_FOUNDATION_INVARIANT

    def test_fix_304_sections_present(self) -> None:
        result = build_channel_integration_foundation(session_id=SESSION)
        sections = result.channel_integration_foundation["sections"]
        for key in (
            "channel_registry",
            "channel_identity_report",
            "channel_authorization_report",
            "channel_capability_matrix",
            "web_channel_report",
            "telegram_channel_report",
            "slack_channel_report",
            "email_channel_report",
            "voice_channel_report",
            "channel_dashboard",
        ):
            assert sections[key]

    def test_fix_304_certification_requirement_count(self) -> None:
        assert len(FIX_304_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_304_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_304_route_id(self) -> None:
        assert CHANNEL_INTEGRATION_FOUNDATION_ROUTE_ID == "mission_control_channel_integration_foundation"

    def test_fix_304_compose_only(self) -> None:
        result = build_channel_integration_foundation(session_id=SESSION)
        sources = result.channel_integration_foundation["sources"]
        assert sources["composes_fix_300_channel_registry"] is True
        assert sources["composes_fix_302_channel_authorization"] is True
        assert sources["automatic_channel_provisioning_performed"] is False
        assert sources["cross_tenant_channel_routing_performed"] is False
        assert sources["channel_specific_governance_performed"] is False
