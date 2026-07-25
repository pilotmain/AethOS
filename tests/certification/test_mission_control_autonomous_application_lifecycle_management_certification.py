# SPDX-License-Identifier: Apache-2.0
"""FIX 280 — autonomous application lifecycle management certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_280_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.autonomous_application_lifecycle_management.autonomous_application_lifecycle_management_contract import (
    AUTOMATIC_LIFECYCLE_EXECUTION_ENABLED_FIX_280,
    AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_FIX,
    AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_INVARIANT,
    AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_PRINCIPLES,
    AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_ROUTE_ID,
    AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_SCHEMA_VERSION,
    DEPLOYMENT_AUTHORITY_FIX_280,
    LIFECYCLE_MANAGEMENT_AUTHORITY_FIX_280,
    ROLLBACK_AUTHORITY_FIX_280,
)
from aethos_core.mission_control.autonomous_application_lifecycle_management.autonomous_application_lifecycle_management_service import (
    build_autonomous_application_lifecycle_management,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface

pytestmark = pytest.mark.certification

SESSION = "mc-aalm-cert-280"


class TestMissionControlAutonomousApplicationLifecycleManagementCertification:
    def test_fix_280_contract(self) -> None:
        assert AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_FIX == "FIX 280"
        assert AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_SCHEMA_VERSION == (
            "mission_control_autonomous_application_lifecycle_management_v1"
        )
        assert LIFECYCLE_MANAGEMENT_AUTHORITY_FIX_280 is False
        assert AUTOMATIC_LIFECYCLE_EXECUTION_ENABLED_FIX_280 is False
        assert DEPLOYMENT_AUTHORITY_FIX_280 is False
        assert ROLLBACK_AUTHORITY_FIX_280 is False

    def test_fix_280_lifecycle_not_execution(self) -> None:
        result = build_autonomous_application_lifecycle_management(session_id=SESSION)
        board = result.autonomous_application_lifecycle_management
        assert set(board["fix_280_certification_requirements"]) == set(FIX_280_CERTIFICATION_REQUIREMENTS)
        assert board["lifecycle_management_authority"] is False
        assert "execution_authority" in AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_INVARIANT

    def test_fix_280_sections_present(self) -> None:
        result = build_autonomous_application_lifecycle_management(session_id=SESSION)
        sections = result.autonomous_application_lifecycle_management["sections"]
        assert sections["lifecycle_stage_registry"]
        assert sections["application_lifecycle_timeline"]
        assert sections["lifecycle_health_dashboard"]
        assert sections["lifecycle_risk_dashboard"]
        assert sections["lifecycle_opportunity_registry"]
        assert sections["application_lifecycle_memory"]
        assert sections["lifecycle_management_dashboard"]
        assert len(AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_PRINCIPLES) >= 10

    def test_fix_280_certification_requirement_count(self) -> None:
        assert len(FIX_280_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_280_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_280_route_id(self) -> None:
        assert AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_ROUTE_ID == (
            "mission_control_autonomous_application_lifecycle_management"
        )

    def test_fix_280_compose_only(self) -> None:
        result = build_autonomous_application_lifecycle_management(session_id=SESSION)
        sources = result.autonomous_application_lifecycle_management["sources"]
        assert sources["pilot_reexecution_performed"] is False
        assert sources["code_generation_performed"] is False
