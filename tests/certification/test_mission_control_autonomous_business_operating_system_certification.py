# SPDX-License-Identifier: Apache-2.0
"""FIX 290 — autonomous business operating system certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_290_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.autonomous_business_operating_system.autonomous_business_operating_system_contract import (
    AUTOMATIC_BUSINESS_EXECUTION_ENABLED_FIX_290,
    AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_FIX,
    AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_INVARIANT,
    AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_PRINCIPLES,
    AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_ROUTE_ID,
    AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_SCHEMA_VERSION,
    BILLING_AUTHORITY_FIX_290,
    BUSINESS_AUTHORITY_FIX_290,
    CUSTOMER_MUTATION_AUTHORITY_FIX_290,
)
from aethos_core.mission_control.autonomous_business_operating_system.autonomous_business_operating_system_service import (
    build_autonomous_business_operating_system,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface

pytestmark = pytest.mark.certification

SESSION = "mc-abos-cert-290"


class TestMissionControlAutonomousBusinessOperatingSystemCertification:
    def test_fix_290_contract(self) -> None:
        assert AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_FIX == "FIX 290"
        assert AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_SCHEMA_VERSION == (
            "mission_control_autonomous_business_operating_system_v1"
        )
        assert BUSINESS_AUTHORITY_FIX_290 is False
        assert AUTOMATIC_BUSINESS_EXECUTION_ENABLED_FIX_290 is False
        assert CUSTOMER_MUTATION_AUTHORITY_FIX_290 is False
        assert BILLING_AUTHORITY_FIX_290 is False

    def test_fix_290_business_not_authority(self) -> None:
        result = build_autonomous_business_operating_system(session_id=SESSION)
        board = result.autonomous_business_operating_system
        assert set(board["fix_290_certification_requirements"]) == set(FIX_290_CERTIFICATION_REQUIREMENTS)
        assert board["business_authority"] is False
        assert "business_authority" in AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_INVARIANT

    def test_fix_290_sections_present(self) -> None:
        result = build_autonomous_business_operating_system(session_id=SESSION)
        sections = result.autonomous_business_operating_system["sections"]
        assert sections["product_portfolio_registry"]
        assert sections["customer_intelligence_registry"]
        assert sections["revenue_intelligence_registry"]
        assert sections["team_operating_registry"]
        assert sections["project_portfolio_registry"]
        assert sections["business_operations_registry"]
        assert sections["business_goal_registry"]
        assert sections["strategic_alignment_graph"]
        assert sections["business_opportunity_portfolio"]
        assert sections["business_health_dashboard"]
        assert sections["business_risk_dashboard"]
        assert sections["business_operating_memory"]
        assert sections["business_operating_dashboard"]
        assert len(AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_PRINCIPLES) >= 10

    def test_fix_290_certification_requirement_count(self) -> None:
        assert len(FIX_290_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_290_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_290_route_id(self) -> None:
        assert AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_ROUTE_ID == (
            "mission_control_autonomous_business_operating_system"
        )

    def test_fix_290_compose_only(self) -> None:
        result = build_autonomous_business_operating_system(session_id=SESSION)
        sources = result.autonomous_business_operating_system["sources"]
        assert sources["pilot_reexecution_performed"] is False
        assert sources["code_generation_performed"] is False
        assert sources["financial_transactions_performed"] is False
        assert sources["customer_mutation_performed"] is False
        assert sources["billing_execution_performed"] is False
