# SPDX-License-Identifier: Apache-2.0
"""FIX 270 — autonomous product stewardship certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_270_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.autonomous_product_stewardship.autonomous_product_stewardship_contract import (
    AUTOMATIC_IMPROVEMENT_ENABLED_FIX_270,
    AUTONOMOUS_PRODUCT_STEWARDSHIP_FIX,
    AUTONOMOUS_PRODUCT_STEWARDSHIP_INVARIANT,
    AUTONOMOUS_PRODUCT_STEWARDSHIP_PRINCIPLES,
    AUTONOMOUS_PRODUCT_STEWARDSHIP_ROUTE_ID,
    AUTONOMOUS_PRODUCT_STEWARDSHIP_SCHEMA_VERSION,
    DEPLOYMENT_AUTHORITY_FIX_270,
    PRODUCT_STEWARDSHIP_AUTHORITY_FIX_270,
    REPOSITORY_MUTATION_AUTHORITY_FIX_270,
)
from aethos_core.mission_control.autonomous_product_stewardship.autonomous_product_stewardship_service import (
    build_autonomous_product_stewardship,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface

pytestmark = pytest.mark.certification

SESSION = "mc-aps-cert-270"


class TestMissionControlAutonomousProductStewardshipCertification:
    def test_fix_270_contract(self) -> None:
        assert AUTONOMOUS_PRODUCT_STEWARDSHIP_FIX == "FIX 270"
        assert AUTONOMOUS_PRODUCT_STEWARDSHIP_SCHEMA_VERSION == (
            "mission_control_autonomous_product_stewardship_v1"
        )
        assert PRODUCT_STEWARDSHIP_AUTHORITY_FIX_270 is False
        assert AUTOMATIC_IMPROVEMENT_ENABLED_FIX_270 is False
        assert REPOSITORY_MUTATION_AUTHORITY_FIX_270 is False
        assert DEPLOYMENT_AUTHORITY_FIX_270 is False

    def test_fix_270_stewardship_not_execution(self) -> None:
        result = build_autonomous_product_stewardship(session_id=SESSION)
        board = result.autonomous_product_stewardship
        assert set(board["fix_270_certification_requirements"]) == set(FIX_270_CERTIFICATION_REQUIREMENTS)
        assert board["product_stewardship_authority"] is False
        assert "execution_authority" in AUTONOMOUS_PRODUCT_STEWARDSHIP_INVARIANT

    def test_fix_270_sections_present(self) -> None:
        result = build_autonomous_product_stewardship(session_id=SESSION)
        sections = result.autonomous_product_stewardship["sections"]
        assert sections["product_health_report"]
        assert sections["engineering_stewardship_report"]
        assert sections["operational_stewardship_report"]
        assert sections["governance_stewardship_report"]
        assert sections["portfolio_stewardship_report"]
        assert sections["stewardship_opportunity_registry"]
        assert sections["stewardship_priority_matrix"]
        assert sections["stewardship_backlog"]
        assert sections["product_stewardship_dashboard"]
        assert sections["product_stewardship_memory"]
        assert len(AUTONOMOUS_PRODUCT_STEWARDSHIP_PRINCIPLES) >= 10

    def test_fix_270_certification_requirement_count(self) -> None:
        assert len(FIX_270_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_270_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_270_route_id(self) -> None:
        assert AUTONOMOUS_PRODUCT_STEWARDSHIP_ROUTE_ID == "mission_control_autonomous_product_stewardship"

    def test_fix_270_compose_only(self) -> None:
        result = build_autonomous_product_stewardship(session_id=SESSION)
        sources = result.autonomous_product_stewardship["sources"]
        assert sources["pilot_reexecution_performed"] is False
        assert sources["code_generation_performed"] is False
