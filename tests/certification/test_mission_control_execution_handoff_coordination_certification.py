# SPDX-License-Identifier: Apache-2.0
"""FIX 167 — execution handoff coordination certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_167,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_167,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_167,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_167,
    EXECUTION_HANDOFF_COORDINATION_FIX,
    EXECUTION_HANDOFF_COORDINATION_SCHEMA_VERSION,
    FORBIDDEN_HANDOFF_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_167,
    HANDOFF_PRINCIPLES,
    HANDOFF_RECOMMENDATION_EXECUTABLE,
    HANDOFF_RECORD_KINDS,
    MERGE_DEPLOY_ENABLED_FIX_167,
    MUTATION_PERFORMED_FIX_167,
    PATH_LANE_MAP,
    PR_OPEN_ENABLED_FIX_167,
    RAILWAY_MUTATION_ENABLED_FIX_167,
)
from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_service import (
    build_execution_handoff_coordination,
)
from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_store import (
    append_execution_handoff_coordination_record,
    clear_execution_handoff_coordination_records_for_tests,
)
from aethos_core.mission_control.human_decision_board.human_decision_board_store import (
    append_human_decision_board_record,
    clear_human_decision_board_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-handoff-cert-167"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_human_decision_board_records_for_tests()
    clear_execution_handoff_coordination_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_human_decision_board_records_for_tests()
    clear_execution_handoff_coordination_records_for_tests()


class TestMissionControlExecutionHandoffCoordinationCertification:
    def test_fix_167_contract(self) -> None:
        assert EXECUTION_HANDOFF_COORDINATION_FIX == "FIX 167"
        assert EXECUTION_HANDOFF_COORDINATION_SCHEMA_VERSION == "mission_control_execution_handoff_coordination_v1"
        assert MUTATION_PERFORMED_FIX_167 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_167 is False
        assert AUTONOMOUS_EXECUTION_ENABLED_FIX_167 is False
        assert AUTONOMOUS_APPROVAL_ENABLED_FIX_167 is False
        assert AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_167 is False
        assert PR_OPEN_ENABLED_FIX_167 is False
        assert MERGE_DEPLOY_ENABLED_FIX_167 is False
        assert RAILWAY_MUTATION_ENABLED_FIX_167 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_167 is False
        assert HANDOFF_RECOMMENDATION_EXECUTABLE is False
        assert "handoff_artifact" in HANDOFF_RECORD_KINDS
        assert len(HANDOFF_PRINCIPLES) >= 8
        assert len(PATH_LANE_MAP) >= 4
        assert len(FORBIDDEN_HANDOFF_ACTIONS) >= 4

    def test_execution_handoff_coordination_cognition_layer(self) -> None:
        _full_stack(SESSION)
        append_human_decision_board_record(
            session_id=SESSION,
            kind="selection_record",
            content="governed_delivery_continuation",
        )
        record, blockers = append_execution_handoff_coordination_record(
            session_id=SESSION,
            kind="handoff_artifact",
            content="Advisory handoff package for governed software delivery lane.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False

        result = build_execution_handoff_coordination(session_id=SESSION)
        assert result.ok is True
        assert result.execution_handoff_coordination["execution_handoff_coordination_cognition"] is True
        assert result.execution_handoff_coordination["handoff_record_count"] == 1
        assert result.execution_handoff_coordination["selected_path_id"] == "governed_delivery_continuation"

    def test_operator_api_includes_execution_handoff_coordination_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/execution-handoff-coordination" in paths
        assert "/mission-control/execution-handoff-coordination/record" in paths
