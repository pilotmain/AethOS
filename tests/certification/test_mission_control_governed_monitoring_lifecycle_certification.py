# SPDX-License-Identifier: Apache-2.0
"""FIX 220 — governed monitoring lifecycle certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_220_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_contract import (
    AUTONOMOUS_REMEDIATION_ENABLED_FIX_220,
    GOVERNED_MONITORING_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_220,
    GOVERNED_MONITORING_LIFECYCLE_FIX,
    GOVERNED_MONITORING_LIFECYCLE_INVARIANT,
    GOVERNED_MONITORING_LIFECYCLE_PRINCIPLES,
    GOVERNED_MONITORING_LIFECYCLE_ROUTE_ID,
    GOVERNED_MONITORING_LIFECYCLE_SCHEMA_VERSION,
    INCIDENT_CLASSIFICATIONS,
    INCIDENT_RESPONSE_AUTHORITY_FIX_220,
    MONITORING_AUTHORITY_FIX_220,
    MONITORING_LIFECYCLE_STAGES,
    ROLLBACK_AUTHORITY_FIX_220,
    WORKFLOW_EXECUTION_AUTHORITY_FIX_220,
)
from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_service import (
    build_governed_monitoring_lifecycle,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from tests.test_mission_control_governed_monitoring_lifecycle import _seed_monitoring_stack

pytestmark = pytest.mark.certification

SESSION = "mc-gmlc-cert-220"


class TestMissionControlGovernedMonitoringLifecycleCertification:
    def test_fix_220_contract(self) -> None:
        assert GOVERNED_MONITORING_LIFECYCLE_FIX == "FIX 220"
        assert GOVERNED_MONITORING_LIFECYCLE_SCHEMA_VERSION == (
            "mission_control_governed_monitoring_lifecycle_v1"
        )
        assert MONITORING_AUTHORITY_FIX_220 is False
        assert INCIDENT_RESPONSE_AUTHORITY_FIX_220 is False
        assert AUTONOMOUS_REMEDIATION_ENABLED_FIX_220 is False
        assert ROLLBACK_AUTHORITY_FIX_220 is False
        assert WORKFLOW_EXECUTION_AUTHORITY_FIX_220 is False
        assert GOVERNED_MONITORING_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_220 is True
        assert len(INCIDENT_CLASSIFICATIONS) == 5
        assert len(MONITORING_LIFECYCLE_STAGES) == 7

    def test_fix_220_monitoring_not_operational_authority(self) -> None:
        _seed_monitoring_stack(SESSION)
        result = build_governed_monitoring_lifecycle(session_id=SESSION)
        report = result.governed_monitoring_lifecycle
        assert set(report["fix_220_certification_requirements"]) == set(FIX_220_CERTIFICATION_REQUIREMENTS)
        assert report["monitoring_authority"] is False
        assert "operational_authority" in GOVERNED_MONITORING_LIFECYCLE_INVARIANT

    def test_fix_220_sections_present(self) -> None:
        _seed_monitoring_stack(SESSION)
        result = build_governed_monitoring_lifecycle(session_id=SESSION)
        sections = result.governed_monitoring_lifecycle["sections"]
        assert sections["monitoring_health_assessment"]
        assert sections["incident_detection"]
        assert sections["monitoring_review_package"]
        assert sections["monitoring_recommendation"]
        assert sections["operational_timeline"]
        assert sections["deployment_health_registry"]
        assert sections["forbidden_monitoring_lifecycle_actions"]
        assert len(GOVERNED_MONITORING_LIFECYCLE_PRINCIPLES) >= 10

    def test_fix_220_certification_requirement_count(self) -> None:
        assert len(FIX_220_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_220_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_220_route_id(self) -> None:
        assert GOVERNED_MONITORING_LIFECYCLE_ROUTE_ID == "mission_control_governed_monitoring_lifecycle"
