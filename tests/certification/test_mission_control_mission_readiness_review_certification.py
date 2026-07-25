# SPDX-License-Identifier: Apache-2.0
"""FIX 147 — mission readiness review board certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.mission_readiness_review.mission_readiness_review_contract import (
    AUTONOMOUS_GO_NO_GO_EXECUTION_ENABLED_FIX_147,
    AUTONOMOUS_READINESS_DECISION_ENABLED_FIX_147,
    EXECUTION_AUTHORITY_DELEGATED_FIX_147,
    GO_NO_GO_HOLD_VALUES,
    HUMAN_REVIEW_REQUIRED_FIX_147,
    MISSION_READINESS_REVIEW_FIX,
    MISSION_READINESS_REVIEW_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_147,
    READINESS_RECOMMENDATION_EXECUTABLE,
)
from aethos_core.mission_control.mission_readiness_review.mission_readiness_review_service import (
    build_mission_readiness_review,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-readiness-cert-147"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()


class TestMissionControlMissionReadinessReviewCertification:
    def test_fix_147_contract(self) -> None:
        assert MISSION_READINESS_REVIEW_FIX == "FIX 147"
        assert MISSION_READINESS_REVIEW_SCHEMA_VERSION == "mission_control_mission_readiness_review_v1"
        assert MUTATION_PERFORMED_FIX_147 is False
        assert HUMAN_REVIEW_REQUIRED_FIX_147 is True
        assert EXECUTION_AUTHORITY_DELEGATED_FIX_147 is False
        assert AUTONOMOUS_GO_NO_GO_EXECUTION_ENABLED_FIX_147 is False
        assert AUTONOMOUS_READINESS_DECISION_ENABLED_FIX_147 is False
        assert READINESS_RECOMMENDATION_EXECUTABLE is False
        assert GO_NO_GO_HOLD_VALUES == ("go", "no-go", "hold")

    def test_mission_readiness_review_advisory_board(self) -> None:
        _full_stack(SESSION)
        result = build_mission_readiness_review(session_id=SESSION)
        assert result.ok is True
        assert result.review["read_only"] is True
        assert result.review["human_review_required"] is True
        go = result.review["sections"]["go_no_go_hold_recommendation"]
        assert go["recommendation"] in GO_NO_GO_HOLD_VALUES
        assert go["advisory_only"] is True

    def test_operator_api_includes_mission_readiness_review_route(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/mission-readiness-review" in paths
