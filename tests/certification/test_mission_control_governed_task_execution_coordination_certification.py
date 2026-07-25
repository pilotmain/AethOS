# SPDX-License-Identifier: Apache-2.0
"""FIX 172 — governed task execution coordination certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_172_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_store import (
    append_bounded_execution_participation_record,
    clear_bounded_execution_participation_records_for_tests,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_store import (
    append_bounded_delivery_work_packages_record,
    clear_bounded_delivery_work_packages_records_for_tests,
)
from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_store import (
    append_execution_handoff_coordination_record,
    clear_execution_handoff_coordination_records_for_tests,
)
from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_172,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_172,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_172,
    CODE_WRITE_ENABLED_FIX_172,
    EXECUTION_PERFORMED_FIX_172,
    FORBIDDEN_COORDINATION_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_172,
    GOVERNANCE_MUTATION_PERFORMED_FIX_172,
    GOVERNED_TASK_EXECUTION_COORDINATION_EXECUTABLE,
    GOVERNED_TASK_EXECUTION_COORDINATION_FIX,
    GOVERNED_TASK_EXECUTION_COORDINATION_INVARIANT,
    GOVERNED_TASK_EXECUTION_COORDINATION_PRINCIPLES,
    GOVERNED_TASK_EXECUTION_COORDINATION_SCHEMA_VERSION,
    MERGE_DEPLOY_ENABLED_FIX_172,
    MUTATION_PERFORMED_FIX_172,
    PR_ACTION_ENABLED_FIX_172,
    RAILWAY_MUTATION_ENABLED_FIX_172,
    TIER_ESCALATION_ENABLED_FIX_172,
)
from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_service import (
    build_governed_task_execution_coordination,
)
from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_store import (
    append_governed_task_execution_coordination_record,
    clear_governed_task_execution_coordination_records_for_tests,
)
from aethos_core.mission_control.human_decision_board.human_decision_board_store import (
    append_human_decision_board_record,
    clear_human_decision_board_records_for_tests,
)
from aethos_core.mission_control.mission_authorization.mission_authorization_store import (
    append_mission_authorization_record,
    clear_mission_authorization_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-gtexec-cert-172"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_human_decision_board_records_for_tests()
    clear_execution_handoff_coordination_records_for_tests()
    clear_bounded_delivery_work_packages_records_for_tests()
    clear_mission_authorization_records_for_tests()
    clear_bounded_execution_participation_records_for_tests()
    clear_governed_task_execution_coordination_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_human_decision_board_records_for_tests()
    clear_execution_handoff_coordination_records_for_tests()
    clear_bounded_delivery_work_packages_records_for_tests()
    clear_mission_authorization_records_for_tests()
    clear_bounded_execution_participation_records_for_tests()
    clear_governed_task_execution_coordination_records_for_tests()


class TestMissionControlGovernedTaskExecutionCoordinationCertification:
    def test_fix_172_contract(self) -> None:
        assert GOVERNED_TASK_EXECUTION_COORDINATION_FIX == "FIX 172"
        assert GOVERNED_TASK_EXECUTION_COORDINATION_SCHEMA_VERSION == (
            "mission_control_governed_task_execution_coordination_v1"
        )
        assert MUTATION_PERFORMED_FIX_172 is False
        assert EXECUTION_PERFORMED_FIX_172 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_172 is False
        assert AUTONOMOUS_EXECUTION_ENABLED_FIX_172 is False
        assert AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_172 is False
        assert TIER_ESCALATION_ENABLED_FIX_172 is False
        assert GATE_BYPASS_ENABLED_FIX_172 is False
        assert CODE_WRITE_ENABLED_FIX_172 is False
        assert PR_ACTION_ENABLED_FIX_172 is False
        assert MERGE_DEPLOY_ENABLED_FIX_172 is False
        assert RAILWAY_MUTATION_ENABLED_FIX_172 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_172 is False
        assert GOVERNED_TASK_EXECUTION_COORDINATION_EXECUTABLE is False
        assert len(GOVERNED_TASK_EXECUTION_COORDINATION_PRINCIPLES) >= 8
        assert len(FORBIDDEN_COORDINATION_ACTIONS) >= 7

    def test_fix_172_governance_friction_certification_requirements(self) -> None:
        _full_stack(SESSION)
        append_human_decision_board_record(
            session_id=SESSION,
            kind="selection_record",
            content="governed_delivery_continuation",
        )
        append_execution_handoff_coordination_record(
            session_id=SESSION,
            kind="handoff_artifact",
            content="Handoff for coordination.",
        )
        append_bounded_delivery_work_packages_record(
            session_id=SESSION,
            kind="work_package_artifact",
            content="Work packages for coordination.",
        )
        append_mission_authorization_record(
            session_id=SESSION,
            kind="mission_authorization_artifact",
            content="Bounded envelope.",
        )
        append_bounded_execution_participation_record(
            session_id=SESSION,
            kind="participation_artifact",
            content="Participation within envelope.",
        )
        result = build_governed_task_execution_coordination(session_id=SESSION)
        assert result.ok is True
        coordination = result.governed_task_execution_coordination

        assert set(coordination["fix_172_certification_requirements"]) == set(FIX_172_CERTIFICATION_REQUIREMENTS)
        assert coordination["coordination_ready"] is True
        assert coordination["execution_performed"] is False

        for row in coordination["sections"]["package_agent_assignments"]:
            if row.get("agent_role_id"):
                assert row.get("execution_authority") is False

        for row in coordination["sections"]["gate_routed_package_outcomes"]:
            assert row.get("gate_bypass") is not True

        assert coordination["autonomous_lane_entry_enabled"] is False
        assert coordination["gate_bypass_enabled"] is False
        assert "coordination" in GOVERNED_TASK_EXECUTION_COORDINATION_INVARIANT.lower()

    def test_governed_task_execution_coordination_cognition_layer(self) -> None:
        _full_stack(SESSION)
        append_human_decision_board_record(
            session_id=SESSION,
            kind="selection_record",
            content="governed_delivery_continuation",
        )
        record, blockers = append_governed_task_execution_coordination_record(
            session_id=SESSION,
            kind="coordination_artifact",
            content="Coordinate packages without executing.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False

        result = build_governed_task_execution_coordination(session_id=SESSION)
        assert result.ok is True
        assert result.governed_task_execution_coordination["governed_task_execution_coordination_cognition"] is True
        assert result.governed_task_execution_coordination["coordination_record_count"] == 1

    def test_operator_api_includes_governed_task_execution_coordination_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/governed-task-execution-coordination" in paths
        assert "/mission-control/governed-task-execution-coordination/record" in paths
