# SPDX-License-Identifier: Apache-2.0
"""FIX 142 — operator guidance certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operator_guidance.operator_guidance_contract import (
    AUTOMATIC_MUTATION_PLANNING_ENABLED_FIX_142,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_142,
    OPERATOR_GUIDANCE_FIX,
    OPERATOR_GUIDANCE_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_142,
    RECOMMENDATION_EXECUTABLE,
)
from aethos_core.mission_control.operator_guidance.operator_guidance_service import build_operator_contextual_guidance
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-guidance-cert-142"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()


class TestMissionControlOperatorGuidanceCertification:
    def test_fix_142_contract(self) -> None:
        assert OPERATOR_GUIDANCE_FIX == "FIX 142"
        assert OPERATOR_GUIDANCE_SCHEMA_VERSION == "mission_control_operator_guidance_v1"
        assert MUTATION_PERFORMED_FIX_142 is False
        assert AUTONOMOUS_EXECUTION_ENABLED_FIX_142 is False
        assert AUTOMATIC_MUTATION_PLANNING_ENABLED_FIX_142 is False
        assert RECOMMENDATION_EXECUTABLE is False

    def test_operator_guidance_recommendation_only(self) -> None:
        _full_stack(SESSION)
        result = build_operator_contextual_guidance(session_id=SESSION)
        assert result.ok is True
        assert result.guidance["read_only"] is True
        assert result.guidance["all_recommendations_executable"] is False

    def test_operator_api_includes_guidance_route(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/operator-guidance" in paths
