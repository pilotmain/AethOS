# SPDX-License-Identifier: Apache-2.0
"""FIX 250 — governed application generation certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_250_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.governed_application_generation.governed_application_generation_contract import (
    APPLICATION_GENERATION_AUTHORITY_FIX_250,
    BOUNDED_GENERATION_AGENT_ROLES,
    CODE_GENERATION_AUTHORITY_FIX_250,
    GENERATION_PIPELINE_STAGES,
    GITHUB_MUTATION_AUTHORITY_FIX_250,
    GOVERNED_APPLICATION_GENERATION_COMPOSES_EVIDENCE_ONLY_FIX_250,
    GOVERNED_APPLICATION_GENERATION_FIX,
    GOVERNED_APPLICATION_GENERATION_INVARIANT,
    GOVERNED_APPLICATION_GENERATION_PRINCIPLES,
    GOVERNED_APPLICATION_GENERATION_ROUTE_ID,
    GOVERNED_APPLICATION_GENERATION_SCHEMA_VERSION,
    REPOSITORY_CREATION_AUTHORITY_FIX_250,
)
from aethos_core.mission_control.governed_application_generation.governed_application_generation_service import (
    build_governed_application_generation,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from tests.test_mission_control_governed_application_generation import _seed_generation_stack

pytestmark = pytest.mark.certification

SESSION = "mc-gag-cert-250"


class TestMissionControlGovernedApplicationGenerationCertification:
    def test_fix_250_contract(self) -> None:
        assert GOVERNED_APPLICATION_GENERATION_FIX == "FIX 250"
        assert GOVERNED_APPLICATION_GENERATION_SCHEMA_VERSION == (
            "mission_control_governed_application_generation_v1"
        )
        assert APPLICATION_GENERATION_AUTHORITY_FIX_250 is False
        assert REPOSITORY_CREATION_AUTHORITY_FIX_250 is False
        assert GITHUB_MUTATION_AUTHORITY_FIX_250 is False
        assert CODE_GENERATION_AUTHORITY_FIX_250 is False
        assert GOVERNED_APPLICATION_GENERATION_COMPOSES_EVIDENCE_ONLY_FIX_250 is True
        assert len(GENERATION_PIPELINE_STAGES) == 6
        assert len(BOUNDED_GENERATION_AGENT_ROLES) == 6

    def test_fix_250_generation_not_autonomous_authority(self) -> None:
        _seed_generation_stack(SESSION)
        result = build_governed_application_generation(session_id=SESSION)
        board = result.governed_application_generation
        assert set(board["fix_250_certification_requirements"]) == set(FIX_250_CERTIFICATION_REQUIREMENTS)
        assert board["application_generation_authority"] is False
        assert "application_generation_authority" in GOVERNED_APPLICATION_GENERATION_INVARIANT

    def test_fix_250_sections_present(self) -> None:
        _seed_generation_stack(SESSION)
        result = build_governed_application_generation(session_id=SESSION)
        sections = result.governed_application_generation["sections"]
        assert sections["product_understanding_package"]
        assert sections["architecture_package"]
        assert sections["repository_blueprint"]
        assert sections["delivery_backlog"]
        assert sections["repository_creation_plan"]
        assert sections["generation_readiness_report"]
        assert sections["generation_memory"]
        assert sections["existing_delivery_pipeline_linkage"]
        assert sections["forbidden_application_generation_actions"]
        assert len(GOVERNED_APPLICATION_GENERATION_PRINCIPLES) >= 10

    def test_fix_250_certification_requirement_count(self) -> None:
        assert len(FIX_250_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_250_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_250_route_id(self) -> None:
        assert GOVERNED_APPLICATION_GENERATION_ROUTE_ID == "mission_control_governed_application_generation"
