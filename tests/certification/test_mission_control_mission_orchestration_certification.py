# SPDX-License-Identifier: Apache-2.0
"""FIX 146 — mission orchestration certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.mission_orchestration.mission_orchestration_contract import (
    AUTONOMOUS_APPROVAL_BATCHING_ENABLED_FIX_146,
    AUTONOMOUS_ORCHESTRATION_ENABLED_FIX_146,
    AUTONOMOUS_PROMOTION_DEPLOY_ENABLED_FIX_146,
    AUTONOMOUS_SEQUENCING_EXECUTION_ENABLED_FIX_146,
    MISSION_ORCHESTRATION_FIX,
    MISSION_ORCHESTRATION_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_146,
    ORCHESTRATION_RECOMMENDATION_EXECUTABLE,
)
from aethos_core.mission_control.mission_orchestration.mission_orchestration_service import (
    build_mission_orchestration,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-orchestration-cert-146"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()


class TestMissionControlMissionOrchestrationCertification:
    def test_fix_146_contract(self) -> None:
        assert MISSION_ORCHESTRATION_FIX == "FIX 146"
        assert MISSION_ORCHESTRATION_SCHEMA_VERSION == "mission_control_mission_orchestration_v1"
        assert MUTATION_PERFORMED_FIX_146 is False
        assert AUTONOMOUS_ORCHESTRATION_ENABLED_FIX_146 is False
        assert AUTONOMOUS_SEQUENCING_EXECUTION_ENABLED_FIX_146 is False
        assert AUTONOMOUS_APPROVAL_BATCHING_ENABLED_FIX_146 is False
        assert AUTONOMOUS_PROMOTION_DEPLOY_ENABLED_FIX_146 is False
        assert ORCHESTRATION_RECOMMENDATION_EXECUTABLE is False

    def test_mission_orchestration_readonly_coordination_layer(self) -> None:
        _full_stack(SESSION)
        result = build_mission_orchestration(session_id=SESSION)
        assert result.ok is True
        assert result.orchestration["read_only"] is True
        assert result.orchestration["sections"]["orchestration_readiness_scoring"]

    def test_operator_api_includes_mission_orchestration_route(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/mission-orchestration" in paths
