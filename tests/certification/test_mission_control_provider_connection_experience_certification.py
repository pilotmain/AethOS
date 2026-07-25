# SPDX-License-Identifier: Apache-2.0
"""FIX 303 — provider connection experience certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_303_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_contract import (
    AUTOMATIC_PROVIDER_CONNECTION_ENABLED_FIX_303,
    PERMISSION_ESCALATION_ENABLED_FIX_303,
    PROVIDER_CONNECTION_AUTHORITY_FIX_303,
    PROVIDER_CONNECTION_EXPERIENCE_FIX,
    PROVIDER_CONNECTION_EXPERIENCE_INVARIANT,
    PROVIDER_CONNECTION_EXPERIENCE_ROUTE_ID,
    PROVIDER_CONNECTION_EXPERIENCE_SCHEMA_VERSION,
    PROVIDER_MUTATION_AUTHORITY_FIX_303,
    SECRET_COLLECTION_ENABLED_FIX_303,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_service import (
    build_provider_connection_experience,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_store import (
    clear_provider_connection_experience_records_for_tests,
)
from aethos_core.orgs.organizations import clear_orgs_for_tests

pytestmark = pytest.mark.certification

SESSION = "mc-pce-cert-303"


@pytest.fixture(autouse=True)
def _clean():
    clear_provider_connection_experience_records_for_tests()
    clear_orgs_for_tests()
    yield
    clear_provider_connection_experience_records_for_tests()
    clear_orgs_for_tests()


class TestMissionControlProviderConnectionExperienceCertification:
    def test_fix_303_contract(self) -> None:
        assert PROVIDER_CONNECTION_EXPERIENCE_FIX == "FIX 303"
        assert PROVIDER_CONNECTION_EXPERIENCE_SCHEMA_VERSION == (
            "mission_control_provider_connection_experience_v1"
        )
        assert PROVIDER_CONNECTION_AUTHORITY_FIX_303 is False
        assert AUTOMATIC_PROVIDER_CONNECTION_ENABLED_FIX_303 is False
        assert PROVIDER_MUTATION_AUTHORITY_FIX_303 is False
        assert SECRET_COLLECTION_ENABLED_FIX_303 is False
        assert PERMISSION_ESCALATION_ENABLED_FIX_303 is False

    def test_fix_303_guidance_not_mutation(self) -> None:
        result = build_provider_connection_experience(session_id=SESSION)
        board = result.provider_connection_experience
        assert set(board["fix_303_certification_requirements"]) == set(FIX_303_CERTIFICATION_REQUIREMENTS)
        assert board["provider_connection_authority"] is False
        assert "mutation_authority" in PROVIDER_CONNECTION_EXPERIENCE_INVARIANT

    def test_fix_303_sections_present(self) -> None:
        result = build_provider_connection_experience(session_id=SESSION)
        sections = result.provider_connection_experience["sections"]
        for key in (
            "provider_connection_dashboard",
            "github_connection_report",
            "railway_connection_report",
            "vercel_connection_report",
            "provider_capability_unlock_matrix",
            "provider_connection_readiness_report",
            "provider_trust_explanation",
        ):
            assert sections[key]

    def test_fix_303_certification_requirement_count(self) -> None:
        assert len(FIX_303_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_303_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_303_route_id(self) -> None:
        assert PROVIDER_CONNECTION_EXPERIENCE_ROUTE_ID == "mission_control_provider_connection_experience"

    def test_fix_303_compose_only(self) -> None:
        result = build_provider_connection_experience(session_id=SESSION)
        sources = result.provider_connection_experience["sources"]
        assert sources["composes_fix_295_provider_capability_matrix"] is True
        assert sources["automatic_provider_connection_performed"] is False
        assert sources["secret_collection_performed"] is False
        assert sources["provider_mutation_performed"] is False
