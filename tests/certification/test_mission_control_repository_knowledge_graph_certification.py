# SPDX-License-Identifier: Apache-2.0
"""FIX 240 — repository knowledge graph certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_240_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.repository_knowledge_graph.repository_knowledge_graph_contract import (
    CODE_MODIFICATION_AUTHORITY_FIX_240,
    CROSS_REPO_AUTHORITY_FIX_240,
    KNOWLEDGE_GRAPH_EXECUTION_FIX_240,
    PHASE_1_KNOWLEDGE_REPOSITORIES,
    REPOSITORY_AUTHORITY_FIX_240,
    REPOSITORY_KNOWLEDGE_GRAPH_COMPOSES_EVIDENCE_ONLY_FIX_240,
    REPOSITORY_KNOWLEDGE_GRAPH_FIX,
    REPOSITORY_KNOWLEDGE_GRAPH_INVARIANT,
    REPOSITORY_KNOWLEDGE_GRAPH_PRINCIPLES,
    REPOSITORY_KNOWLEDGE_GRAPH_ROUTE_ID,
    REPOSITORY_KNOWLEDGE_GRAPH_SCHEMA_VERSION,
)
from aethos_core.mission_control.repository_knowledge_graph.repository_knowledge_graph_service import (
    build_repository_knowledge_graph,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from tests.test_mission_control_repository_knowledge_graph import _seed_knowledge_graph_stack

pytestmark = pytest.mark.certification

SESSION = "mc-rkg-cert-240"


class TestMissionControlRepositoryKnowledgeGraphCertification:
    def test_fix_240_contract(self) -> None:
        assert REPOSITORY_KNOWLEDGE_GRAPH_FIX == "FIX 240"
        assert REPOSITORY_KNOWLEDGE_GRAPH_SCHEMA_VERSION == "mission_control_repository_knowledge_graph_v1"
        assert REPOSITORY_AUTHORITY_FIX_240 is False
        assert CODE_MODIFICATION_AUTHORITY_FIX_240 is False
        assert CROSS_REPO_AUTHORITY_FIX_240 is False
        assert KNOWLEDGE_GRAPH_EXECUTION_FIX_240 is False
        assert REPOSITORY_KNOWLEDGE_GRAPH_COMPOSES_EVIDENCE_ONLY_FIX_240 is True
        assert len(PHASE_1_KNOWLEDGE_REPOSITORIES) == 4

    def test_fix_240_intelligence_not_authority(self) -> None:
        _seed_knowledge_graph_stack(SESSION)
        result = build_repository_knowledge_graph(session_id=SESSION)
        graph = result.repository_knowledge_graph
        assert set(graph["fix_240_certification_requirements"]) == set(FIX_240_CERTIFICATION_REQUIREMENTS)
        assert graph["repository_authority"] is False
        assert "repository_authority" in REPOSITORY_KNOWLEDGE_GRAPH_INVARIANT

    def test_fix_240_sections_present(self) -> None:
        _seed_knowledge_graph_stack(SESSION)
        result = build_repository_knowledge_graph(session_id=SESSION)
        sections = result.repository_knowledge_graph["sections"]
        assert sections["architecture_graph"]
        assert sections["dependency_registry"]
        assert sections["dependency_risk_report"]
        assert sections["ownership_registry"]
        assert sections["ownership_confidence"]
        assert sections["historical_change_report"]
        assert sections["repository_hotspot_map"]
        assert sections["change_impact_assessment"]
        assert sections["repository_risk_profile"]
        assert sections["engineering_intelligence_dashboard"]
        assert sections["cross_repository_knowledge"]
        assert sections["repository_memory"]
        assert len(REPOSITORY_KNOWLEDGE_GRAPH_PRINCIPLES) >= 10

    def test_fix_240_certification_requirement_count(self) -> None:
        assert len(FIX_240_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_240_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_240_route_id(self) -> None:
        assert REPOSITORY_KNOWLEDGE_GRAPH_ROUTE_ID == "mission_control_repository_knowledge_graph"
