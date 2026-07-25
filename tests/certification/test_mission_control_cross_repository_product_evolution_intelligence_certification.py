# SPDX-License-Identifier: Apache-2.0
"""FIX 261 — cross-repository product evolution intelligence certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_261_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.cross_repository_product_evolution_intelligence.cross_repository_product_evolution_intelligence_contract import (
    AUTOMATIC_IMPROVEMENT_ENABLED_FIX_261,
    CROSS_REPO_EXECUTION_ENABLED_FIX_261,
    CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_FIX,
    CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_INVARIANT,
    CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_PRINCIPLES,
    CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_ROUTE_ID,
    CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_SCHEMA_VERSION,
    PRODUCT_EVOLUTION_AUTHORITY_FIX_261,
    REPOSITORY_MUTATION_AUTHORITY_FIX_261,
)
from aethos_core.mission_control.cross_repository_product_evolution_intelligence.cross_repository_product_evolution_intelligence_service import (
    build_cross_repository_product_evolution_intelligence,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface

pytestmark = pytest.mark.certification

SESSION = "mc-crpei-cert-261"


class TestMissionControlCrossRepositoryProductEvolutionIntelligenceCertification:
    def test_fix_261_contract(self) -> None:
        assert CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_FIX == "FIX 261"
        assert CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_SCHEMA_VERSION == (
            "mission_control_cross_repository_product_evolution_intelligence_v1"
        )
        assert PRODUCT_EVOLUTION_AUTHORITY_FIX_261 is False
        assert AUTOMATIC_IMPROVEMENT_ENABLED_FIX_261 is False
        assert CROSS_REPO_EXECUTION_ENABLED_FIX_261 is False
        assert REPOSITORY_MUTATION_AUTHORITY_FIX_261 is False

    def test_fix_261_evolution_not_execution(self) -> None:
        result = build_cross_repository_product_evolution_intelligence(session_id=SESSION)
        board = result.cross_repository_product_evolution_intelligence
        assert set(board["fix_261_certification_requirements"]) == set(FIX_261_CERTIFICATION_REQUIREMENTS)
        assert board["product_evolution_authority"] is False
        assert "execution_authority" in CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_INVARIANT

    def test_fix_261_sections_present(self) -> None:
        result = build_cross_repository_product_evolution_intelligence(session_id=SESSION)
        sections = result.cross_repository_product_evolution_intelligence["sections"]
        assert sections["feature_evolution_report"]
        assert sections["quality_evolution_report"]
        assert sections["architecture_evolution_report"]
        assert sections["operational_evolution_report"]
        assert sections["ux_evolution_report"]
        assert sections["opportunity_graph"]
        assert sections["portfolio_evolution_backlog"]
        assert sections["evolution_priority_matrix"]
        assert sections["product_evolution_dashboard"]
        assert len(CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_PRINCIPLES) >= 10

    def test_fix_261_certification_requirement_count(self) -> None:
        assert len(FIX_261_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_261_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_261_route_id(self) -> None:
        assert CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_ROUTE_ID == (
            "mission_control_cross_repository_product_evolution_intelligence"
        )

    def test_fix_261_compose_only(self) -> None:
        result = build_cross_repository_product_evolution_intelligence(session_id=SESSION)
        sources = result.cross_repository_product_evolution_intelligence["sources"]
        assert sources["pilot_reexecution_performed"] is False
        assert sources["code_generation_performed"] is False
