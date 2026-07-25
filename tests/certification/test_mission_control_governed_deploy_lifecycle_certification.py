# SPDX-License-Identifier: Apache-2.0
"""FIX 210 — governed deploy lifecycle certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_210_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_contract import (
    AUTONOMOUS_DEPLOY_ENABLED_FIX_210,
    AWS_AUTHORITY_FIX_210,
    DEPLOY_AUTHORITY_FIX_210,
    DEPLOY_LIFECYCLE_STAGES,
    GOVERNED_DEPLOY_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_210,
    GOVERNED_DEPLOY_LIFECYCLE_FIX,
    GOVERNED_DEPLOY_LIFECYCLE_INVARIANT,
    GOVERNED_DEPLOY_LIFECYCLE_PRINCIPLES,
    GOVERNED_DEPLOY_LIFECYCLE_ROUTE_ID,
    GOVERNED_DEPLOY_LIFECYCLE_SCHEMA_VERSION,
    KUBERNETES_AUTHORITY_FIX_210,
    PHASE_1_DEPLOY_ENVIRONMENTS,
    RAILWAY_AUTHORITY_FIX_210,
    VERCEL_AUTHORITY_FIX_210,
    WORKFLOW_EXECUTION_PERFORMED_FIX_210,
)
from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_service import (
    build_governed_deploy_lifecycle,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from tests.test_mission_control_governed_deploy_lifecycle import _seed_deploy_lifecycle_stack

pytestmark = pytest.mark.certification

SESSION = "mc-gdl-cert-210"


class TestMissionControlGovernedDeployLifecycleCertification:
    def test_fix_210_contract(self) -> None:
        assert GOVERNED_DEPLOY_LIFECYCLE_FIX == "FIX 210"
        assert GOVERNED_DEPLOY_LIFECYCLE_SCHEMA_VERSION == "mission_control_governed_deploy_lifecycle_v1"
        assert DEPLOY_AUTHORITY_FIX_210 is False
        assert AUTONOMOUS_DEPLOY_ENABLED_FIX_210 is False
        assert WORKFLOW_EXECUTION_PERFORMED_FIX_210 is False
        assert RAILWAY_AUTHORITY_FIX_210 is False
        assert VERCEL_AUTHORITY_FIX_210 is False
        assert AWS_AUTHORITY_FIX_210 is False
        assert KUBERNETES_AUTHORITY_FIX_210 is False
        assert GOVERNED_DEPLOY_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_210 is True
        assert PHASE_1_DEPLOY_ENVIRONMENTS == ("development", "staging")
        assert len(DEPLOY_LIFECYCLE_STAGES) == 7

    def test_fix_210_deploy_not_autonomous(self) -> None:
        _seed_deploy_lifecycle_stack(SESSION)
        result = build_governed_deploy_lifecycle(session_id=SESSION)
        report = result.governed_deploy_lifecycle
        assert set(report["fix_210_certification_requirements"]) == set(FIX_210_CERTIFICATION_REQUIREMENTS)
        assert report["deploy_authority"] is False
        assert "autonomous_deploy" in GOVERNED_DEPLOY_LIFECYCLE_INVARIANT

    def test_fix_210_sections_present(self) -> None:
        _seed_deploy_lifecycle_stack(SESSION)
        result = build_governed_deploy_lifecycle(session_id=SESSION)
        sections = result.governed_deploy_lifecycle["sections"]
        assert sections["deploy_readiness_assessment"]
        assert sections["deploy_review_package"]
        assert sections["deploy_recommendation"]
        assert sections["github_actions_deployment_adapter"]
        assert sections["post_deploy_audit"]
        assert sections["forbidden_deploy_lifecycle_actions"]
        assert len(GOVERNED_DEPLOY_LIFECYCLE_PRINCIPLES) >= 10

    def test_fix_210_certification_requirement_count(self) -> None:
        assert len(FIX_210_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_210_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_210_route_id(self) -> None:
        assert GOVERNED_DEPLOY_LIFECYCLE_ROUTE_ID == "mission_control_governed_deploy_lifecycle"
