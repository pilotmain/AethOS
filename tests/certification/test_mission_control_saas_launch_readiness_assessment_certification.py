# SPDX-License-Identifier: Apache-2.0
"""FIX 309 — SaaS launch readiness assessment certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_309_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_contract import (
    AUTOMATIC_LAUNCH_ENABLED_FIX_309,
    AUTOMATIC_READINESS_PROMOTION_ENABLED_FIX_309,
    CUSTOMER_PROVISIONING_AUTHORITY_FIX_309,
    LAUNCH_AUTHORITY_FIX_309,
    SAAS_LAUNCH_READINESS_ASSESSMENT_FIX,
    SAAS_LAUNCH_READINESS_ASSESSMENT_INVARIANT,
    SAAS_LAUNCH_READINESS_ASSESSMENT_ROUTE_ID,
    SAAS_LAUNCH_READINESS_ASSESSMENT_SCHEMA_VERSION,
    TRUST_MUTATION_AUTHORITY_FIX_309,
)
from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_service import (
    build_saas_launch_readiness_assessment,
)
from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_store import (
    clear_saas_launch_readiness_assessment_records_for_tests,
)
from aethos_core.orgs.organizations import clear_orgs_for_tests

pytestmark = pytest.mark.certification

SESSION = "mc-slra-cert-309"


@pytest.fixture(autouse=True)
def _clean():
    clear_saas_launch_readiness_assessment_records_for_tests()
    clear_orgs_for_tests()
    yield
    clear_saas_launch_readiness_assessment_records_for_tests()
    clear_orgs_for_tests()


class TestMissionControlSaasLaunchReadinessAssessmentCertification:
    def test_fix_309_contract(self) -> None:
        assert SAAS_LAUNCH_READINESS_ASSESSMENT_FIX == "FIX 309"
        assert SAAS_LAUNCH_READINESS_ASSESSMENT_SCHEMA_VERSION == (
            "mission_control_saas_launch_readiness_assessment_v1"
        )
        assert LAUNCH_AUTHORITY_FIX_309 is False
        assert AUTOMATIC_LAUNCH_ENABLED_FIX_309 is False
        assert AUTOMATIC_READINESS_PROMOTION_ENABLED_FIX_309 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_309 is False
        assert CUSTOMER_PROVISIONING_AUTHORITY_FIX_309 is False

    def test_fix_309_assessment_not_authority(self) -> None:
        result = build_saas_launch_readiness_assessment(session_id=SESSION)
        board = result.saas_launch_readiness_assessment
        assert set(board["fix_309_certification_requirements"]) == set(FIX_309_CERTIFICATION_REQUIREMENTS)
        assert board["launch_authority"] is False
        assert "assessment" in SAAS_LAUNCH_READINESS_ASSESSMENT_INVARIANT

    def test_fix_309_sections_present(self) -> None:
        result = build_saas_launch_readiness_assessment(session_id=SESSION)
        sections = result.saas_launch_readiness_assessment["sections"]
        for key in (
            "product_readiness_report",
            "platform_readiness_report",
            "security_readiness_report",
            "governance_readiness_report",
            "operational_readiness_report",
            "commercial_readiness_report",
            "customer_readiness_report",
            "support_readiness_report",
            "launch_risk_registry",
            "launch_readiness_dashboard",
        ):
            assert sections[key]

    def test_fix_309_certification_requirement_count(self) -> None:
        assert len(FIX_309_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_309_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_309_route_id(self) -> None:
        assert SAAS_LAUNCH_READINESS_ASSESSMENT_ROUTE_ID == "mission_control_saas_launch_readiness_assessment"

    def test_fix_309_compose_only(self) -> None:
        result = build_saas_launch_readiness_assessment(session_id=SESSION)
        sources = result.saas_launch_readiness_assessment["sources"]
        assert sources["composes_fix_300_through_308"] is True
        assert sources["launch_declaration_performed"] is False
        assert sources["customer_provisioning_performed"] is False
        assert sources["pilot_reexecution_performed"] is False
