# SPDX-License-Identifier: Apache-2.0
"""FIX 230 — governed rollback lifecycle certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_230_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_contract import (
    AUTONOMOUS_ROLLBACK_ENABLED_FIX_230,
    DATABASE_MUTATION_AUTHORITY_FIX_230,
    GOVERNED_ROLLBACK_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_230,
    GOVERNED_ROLLBACK_LIFECYCLE_FIX,
    GOVERNED_ROLLBACK_LIFECYCLE_INVARIANT,
    GOVERNED_ROLLBACK_LIFECYCLE_PRINCIPLES,
    GOVERNED_ROLLBACK_LIFECYCLE_ROUTE_ID,
    GOVERNED_ROLLBACK_LIFECYCLE_SCHEMA_VERSION,
    HIDDEN_RECOVERY_PATH_ENABLED_FIX_230,
    ROLLBACK_AUTHORITY_FIX_230,
    ROLLBACK_LIFECYCLE_STAGES,
    ROLLBACK_RECOMMENDATIONS,
    WORKFLOW_EXECUTION_PERFORMED_FIX_230,
)
from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_service import (
    build_governed_rollback_lifecycle,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from tests.test_mission_control_governed_rollback_lifecycle import _seed_rollback_stack

pytestmark = pytest.mark.certification

SESSION = "mc-grlc-cert-230"


class TestMissionControlGovernedRollbackLifecycleCertification:
    def test_fix_230_contract(self) -> None:
        assert GOVERNED_ROLLBACK_LIFECYCLE_FIX == "FIX 230"
        assert GOVERNED_ROLLBACK_LIFECYCLE_SCHEMA_VERSION == (
            "mission_control_governed_rollback_lifecycle_v1"
        )
        assert ROLLBACK_AUTHORITY_FIX_230 is False
        assert AUTONOMOUS_ROLLBACK_ENABLED_FIX_230 is False
        assert WORKFLOW_EXECUTION_PERFORMED_FIX_230 is False
        assert DATABASE_MUTATION_AUTHORITY_FIX_230 is False
        assert HIDDEN_RECOVERY_PATH_ENABLED_FIX_230 is False
        assert GOVERNED_ROLLBACK_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_230 is True
        assert len(ROLLBACK_RECOMMENDATIONS) == 4
        assert len(ROLLBACK_LIFECYCLE_STAGES) == 8

    def test_fix_230_rollback_not_autonomous(self) -> None:
        _seed_rollback_stack(SESSION)
        result = build_governed_rollback_lifecycle(session_id=SESSION)
        report = result.governed_rollback_lifecycle
        assert set(report["fix_230_certification_requirements"]) == set(FIX_230_CERTIFICATION_REQUIREMENTS)
        assert report["rollback_authority"] is False
        assert "autonomous_rollback" in GOVERNED_ROLLBACK_LIFECYCLE_INVARIANT

    def test_fix_230_sections_present(self) -> None:
        _seed_rollback_stack(SESSION)
        result = build_governed_rollback_lifecycle(session_id=SESSION)
        sections = result.governed_rollback_lifecycle["sections"]
        assert sections["rollback_assessment"]
        assert sections["rollback_candidate_registry"]
        assert sections["rollback_risk_summary"]
        assert sections["rollback_review_package"]
        assert sections["rollback_recommendation"]
        assert sections["recovery_timeline"]
        assert sections["forbidden_rollback_lifecycle_actions"]
        assert len(GOVERNED_ROLLBACK_LIFECYCLE_PRINCIPLES) >= 10

    def test_fix_230_certification_requirement_count(self) -> None:
        assert len(FIX_230_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_230_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_230_route_id(self) -> None:
        assert GOVERNED_ROLLBACK_LIFECYCLE_ROUTE_ID == "mission_control_governed_rollback_lifecycle"
