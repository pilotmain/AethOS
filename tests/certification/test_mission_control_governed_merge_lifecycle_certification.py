# SPDX-License-Identifier: Apache-2.0
"""FIX 200 — governed merge lifecycle certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_200_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_contract import (
    APPROVAL_BYPASS_ENABLED_FIX_200,
    AUTONOMOUS_MERGE_ENABLED_FIX_200,
    GOVERNED_MERGE_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_200,
    GOVERNED_MERGE_LIFECYCLE_FIX,
    GOVERNED_MERGE_LIFECYCLE_INVARIANT,
    GOVERNED_MERGE_LIFECYCLE_PRINCIPLES,
    GOVERNED_MERGE_LIFECYCLE_ROUTE_ID,
    GOVERNED_MERGE_LIFECYCLE_SCHEMA_VERSION,
    MERGE_AUTHORITY_FIX_200,
    MERGE_EXECUTION_PERFORMED_FIX_200,
    MERGE_LIFECYCLE_STAGES,
)
from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_service import (
    build_governed_merge_lifecycle,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from tests.test_mission_control_governed_merge_lifecycle import _seed_merge_lifecycle_stack

pytestmark = pytest.mark.certification

SESSION = "mc-gml-cert-200"


class TestMissionControlGovernedMergeLifecycleCertification:
    def test_fix_200_contract(self) -> None:
        assert GOVERNED_MERGE_LIFECYCLE_FIX == "FIX 200"
        assert GOVERNED_MERGE_LIFECYCLE_SCHEMA_VERSION == "mission_control_governed_merge_lifecycle_v1"
        assert MERGE_AUTHORITY_FIX_200 is False
        assert AUTONOMOUS_MERGE_ENABLED_FIX_200 is False
        assert APPROVAL_BYPASS_ENABLED_FIX_200 is False
        assert MERGE_EXECUTION_PERFORMED_FIX_200 is False
        assert GOVERNED_MERGE_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_200 is True
        assert len(MERGE_LIFECYCLE_STAGES) == 6
        assert len(GOVERNED_MERGE_LIFECYCLE_PRINCIPLES) >= 8

    def test_fix_200_merge_not_autonomous(self) -> None:
        _seed_merge_lifecycle_stack(SESSION)
        result = build_governed_merge_lifecycle(session_id=SESSION)
        report = result.governed_merge_lifecycle
        assert set(report["fix_200_certification_requirements"]) == set(FIX_200_CERTIFICATION_REQUIREMENTS)
        assert report["merge_authority"] is False
        assert "autonomous_merge" in GOVERNED_MERGE_LIFECYCLE_INVARIANT

    def test_fix_200_sections_present(self) -> None:
        _seed_merge_lifecycle_stack(SESSION)
        result = build_governed_merge_lifecycle(session_id=SESSION)
        sections = result.governed_merge_lifecycle["sections"]
        assert sections["merge_readiness_assessment"]
        assert sections["merge_review_package"]
        assert sections["merge_recommendation"]
        assert sections["merge_execution_adapter"]
        assert sections["post_merge_audit"]
        assert sections["forbidden_merge_lifecycle_actions"]

    def test_fix_200_certification_requirement_count(self) -> None:
        assert len(FIX_200_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_200_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_200_route_id(self) -> None:
        assert GOVERNED_MERGE_LIFECYCLE_ROUTE_ID == "mission_control_governed_merge_lifecycle"
