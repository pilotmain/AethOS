# SPDX-License-Identifier: Apache-2.0
"""FIX 260 — multi-repository engineering intelligence certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_260_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_contract import (
    CROSS_REPO_AUTHORITY_FIX_260,
    MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_COMPOSES_EVIDENCE_ONLY_FIX_260,
    MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_FIX,
    MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_INVARIANT,
    MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_PRINCIPLES,
    MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_ROUTE_ID,
    MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_SCHEMA_VERSION,
    PORTFOLIO_AUTHORITY_FIX_260,
    PORTFOLIO_REPOSITORIES,
    PROGRAM_DELIVERY_AUTHORITY_FIX_260,
)
from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_service import (
    build_multi_repository_engineering_intelligence,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface

pytestmark = pytest.mark.certification

SESSION = "mc-mrei-cert-260"


class TestMissionControlMultiRepositoryEngineeringIntelligenceCertification:
    def test_fix_260_contract(self) -> None:
        assert MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_FIX == "FIX 260"
        assert MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_SCHEMA_VERSION == (
            "mission_control_multi_repository_engineering_intelligence_v1"
        )
        assert PORTFOLIO_AUTHORITY_FIX_260 is False
        assert CROSS_REPO_AUTHORITY_FIX_260 is False
        assert PROGRAM_DELIVERY_AUTHORITY_FIX_260 is False
        assert MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_COMPOSES_EVIDENCE_ONLY_FIX_260 is True
        assert len(PORTFOLIO_REPOSITORIES) == 4

    def test_fix_260_portfolio_not_authority(self) -> None:
        result = build_multi_repository_engineering_intelligence(session_id=SESSION)
        board = result.multi_repository_engineering_intelligence
        assert set(board["fix_260_certification_requirements"]) == set(FIX_260_CERTIFICATION_REQUIREMENTS)
        assert board["portfolio_authority"] is False
        assert "cross_repo_authority" in MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_INVARIANT

    def test_fix_260_sections_present(self) -> None:
        result = build_multi_repository_engineering_intelligence(session_id=SESSION)
        sections = result.multi_repository_engineering_intelligence["sections"]
        assert sections["portfolio_engineering_dashboard"]
        assert sections["cross_repository_dependency_map"]
        assert sections["engineering_health_scores"]
        assert sections["program_delivery_visibility"]
        assert sections["repository_knowledge_signals"]
        assert sections["forbidden_intelligence_actions"]
        assert len(MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_PRINCIPLES) >= 10

    def test_fix_260_certification_requirement_count(self) -> None:
        assert len(FIX_260_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_260_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_260_route_id(self) -> None:
        assert MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_ROUTE_ID == (
            "mission_control_multi_repository_engineering_intelligence"
        )

    def test_fix_260_sources_compose_only(self) -> None:
        result = build_multi_repository_engineering_intelligence(session_id=SESSION)
        sources = result.multi_repository_engineering_intelligence["sources"]
        assert sources["composes_fix_191_cross_repo_validation"] is True
        assert sources["pilot_reexecution_performed"] is False
