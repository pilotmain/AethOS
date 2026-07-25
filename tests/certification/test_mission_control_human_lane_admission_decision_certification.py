# SPDX-License-Identifier: Apache-2.0
"""FIX 176 — human lane admission decision certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_176_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_store import (
    clear_governed_lane_readiness_board_records_for_tests,
)
from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_176,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_176,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_176,
    CODE_WRITE_ENABLED_FIX_176,
    EXECUTION_PERFORMED_FIX_176,
    FORBIDDEN_DECISION_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_176,
    GOVERNANCE_MUTATION_PERFORMED_FIX_176,
    HUMAN_LANE_ADMISSION_DECISION_FIX,
    HUMAN_LANE_ADMISSION_DECISION_INVARIANT,
    HUMAN_LANE_ADMISSION_DECISION_PRINCIPLES,
    HUMAN_LANE_ADMISSION_DECISION_SCHEMA_VERSION,
    LANE_ADMISSION_EXECUTED_FIX_176,
    LANE_ENTRY_EXECUTION_PERFORMED_FIX_176,
    MERGE_DEPLOY_ENABLED_FIX_176,
    MUTATION_PERFORMED_FIX_176,
    PR_ACTION_ENABLED_FIX_176,
    RAILWAY_MUTATION_ENABLED_FIX_176,
    TIER_ESCALATION_ENABLED_FIX_176,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_175,
)
from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_service import (
    build_human_lane_admission_decision,
)
from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_store import (
    append_human_lane_admission_decision_record,
    clear_human_lane_admission_decision_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_mission_control_governed_lane_readiness_board import _lane_board_stack

pytestmark = pytest.mark.certification

SESSION = "mc-hlad-cert-176"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_store import (
        clear_bounded_execution_participation_records_for_tests,
    )
    from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_store import (
        clear_bounded_delivery_work_packages_records_for_tests,
    )
    from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_store import (
        clear_execution_handoff_coordination_records_for_tests,
    )
    from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_store import (
        clear_governed_task_execution_coordination_records_for_tests,
    )
    from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_store import (
        clear_gate_routed_package_outcome_review_records_for_tests,
    )
    from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_store import (
        clear_governed_lane_entry_recommendation_records_for_tests,
    )
    from aethos_core.mission_control.human_decision_board.human_decision_board_store import (
        clear_human_decision_board_records_for_tests,
    )
    from aethos_core.mission_control.mission_authorization.mission_authorization_store import (
        clear_mission_authorization_records_for_tests,
    )
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_human_decision_board_records_for_tests()
    clear_execution_handoff_coordination_records_for_tests()
    clear_bounded_delivery_work_packages_records_for_tests()
    clear_mission_authorization_records_for_tests()
    clear_bounded_execution_participation_records_for_tests()
    clear_governed_task_execution_coordination_records_for_tests()
    clear_gate_routed_package_outcome_review_records_for_tests()
    clear_governed_lane_entry_recommendation_records_for_tests()
    clear_governed_lane_readiness_board_records_for_tests()
    clear_human_lane_admission_decision_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_human_decision_board_records_for_tests()
    clear_execution_handoff_coordination_records_for_tests()
    clear_bounded_delivery_work_packages_records_for_tests()
    clear_mission_authorization_records_for_tests()
    clear_bounded_execution_participation_records_for_tests()
    clear_governed_task_execution_coordination_records_for_tests()
    clear_gate_routed_package_outcome_review_records_for_tests()
    clear_governed_lane_entry_recommendation_records_for_tests()
    clear_governed_lane_readiness_board_records_for_tests()
    clear_human_lane_admission_decision_records_for_tests()


class TestMissionControlHumanLaneAdmissionDecisionCertification:
    def test_fix_176_contract(self) -> None:
        assert HUMAN_LANE_ADMISSION_DECISION_FIX == "FIX 176"
        assert HUMAN_LANE_ADMISSION_DECISION_SCHEMA_VERSION == (
            "mission_control_human_lane_admission_decision_v1"
        )
        assert MUTATION_PERFORMED_FIX_176 is False
        assert EXECUTION_PERFORMED_FIX_176 is False
        assert LANE_ENTRY_EXECUTION_PERFORMED_FIX_176 is False
        assert LANE_ADMISSION_EXECUTED_FIX_176 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_176 is False
        assert AUTONOMOUS_EXECUTION_ENABLED_FIX_176 is False
        assert AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_176 is False
        assert TIER_ESCALATION_ENABLED_FIX_176 is False
        assert GATE_BYPASS_ENABLED_FIX_176 is False
        assert CODE_WRITE_ENABLED_FIX_176 is False
        assert PR_ACTION_ENABLED_FIX_176 is False
        assert MERGE_DEPLOY_ENABLED_FIX_176 is False
        assert RAILWAY_MUTATION_ENABLED_FIX_176 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_176 is False
        assert len(HUMAN_LANE_ADMISSION_DECISION_PRINCIPLES) >= 9
        assert len(FORBIDDEN_DECISION_ACTIONS) >= 10
        assert "board_recompute" in {a for a, _ in FORBIDDEN_DECISION_ACTIONS}

    def test_fix_176_composes_upstream_without_duplication(self) -> None:
        _lane_board_stack(SESSION)
        result = build_human_lane_admission_decision(session_id=SESSION)
        assert result.ok is True
        decision = result.human_lane_admission_decision

        assert set(decision["fix_176_certification_requirements"]) == set(FIX_176_CERTIFICATION_REQUIREMENTS)
        assert decision["composes_upstream_layers_not_duplicates"] is True
        assert decision["sources"]["composes_governed_lane_readiness_board"] is True

        section_keys = set(decision.get("sections") or {})
        assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_175)

        board_read = decision["sections"]["lane_readiness_board_upstream_read"][0]
        assert board_read.get("recomputed_by_fix_176") is False

        assert decision["lane_entry_execution_performed"] is False
        assert decision["lane_admission_executed"] is False
        assert "decision" in HUMAN_LANE_ADMISSION_DECISION_INVARIANT.lower()

    def test_human_lane_admission_decision_cognition_layer(self) -> None:
        _lane_board_stack(SESSION)
        record, blockers = append_human_lane_admission_decision_record(
            session_id=SESSION,
            kind="lane_admission_decision_record",
            content="hold: pending additional verification evidence",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False
        assert record.get("lane_entry_execution_performed") is False

        result = build_human_lane_admission_decision(session_id=SESSION)
        assert result.ok is True
        assert result.human_lane_admission_decision["human_lane_admission_decision_cognition"] is True
        assert result.human_lane_admission_decision["human_decision_recorded"] is True

    def test_operator_api_includes_human_lane_admission_decision_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/human-lane-admission-decision" in paths
        assert "/mission-control/human-lane-admission-decision/record" in paths
