# SPDX-License-Identifier: Apache-2.0
"""FIX 175 — governed lane readiness board certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_175_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_store import (
    append_governed_lane_entry_recommendation_record,
    clear_governed_lane_entry_recommendation_records_for_tests,
)
from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_175,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_175,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_175,
    CODE_WRITE_ENABLED_FIX_175,
    EXECUTION_PERFORMED_FIX_175,
    FORBIDDEN_BOARD_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_175,
    GOVERNANCE_MUTATION_PERFORMED_FIX_175,
    GOVERNED_LANE_READINESS_BOARD_FIX,
    GOVERNED_LANE_READINESS_BOARD_INVARIANT,
    GOVERNED_LANE_READINESS_BOARD_PRINCIPLES,
    GOVERNED_LANE_READINESS_BOARD_SCHEMA_VERSION,
    LANE_ADMISSION_DECISION_PERFORMED_FIX_175,
    LANE_ADMISSION_PERFORMED_FIX_175,
    MERGE_DEPLOY_ENABLED_FIX_175,
    MUTATION_PERFORMED_FIX_175,
    PR_ACTION_ENABLED_FIX_175,
    RAILWAY_MUTATION_ENABLED_FIX_175,
    TIER_ESCALATION_ENABLED_FIX_175,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_174,
)
from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_service import (
    build_governed_lane_readiness_board,
)
from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_store import (
    append_governed_lane_readiness_board_record,
    clear_governed_lane_readiness_board_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_mission_control_gate_routed_package_outcome_review import _gate_review_stack

pytestmark = pytest.mark.certification

SESSION = "mc-glrb-cert-175"


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


class TestMissionControlGovernedLaneReadinessBoardCertification:
    def test_fix_175_contract(self) -> None:
        assert GOVERNED_LANE_READINESS_BOARD_FIX == "FIX 175"
        assert GOVERNED_LANE_READINESS_BOARD_SCHEMA_VERSION == (
            "mission_control_governed_lane_readiness_board_v1"
        )
        assert MUTATION_PERFORMED_FIX_175 is False
        assert EXECUTION_PERFORMED_FIX_175 is False
        assert LANE_ADMISSION_PERFORMED_FIX_175 is False
        assert LANE_ADMISSION_DECISION_PERFORMED_FIX_175 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_175 is False
        assert AUTONOMOUS_EXECUTION_ENABLED_FIX_175 is False
        assert AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_175 is False
        assert TIER_ESCALATION_ENABLED_FIX_175 is False
        assert GATE_BYPASS_ENABLED_FIX_175 is False
        assert CODE_WRITE_ENABLED_FIX_175 is False
        assert PR_ACTION_ENABLED_FIX_175 is False
        assert MERGE_DEPLOY_ENABLED_FIX_175 is False
        assert RAILWAY_MUTATION_ENABLED_FIX_175 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_175 is False
        assert len(GOVERNED_LANE_READINESS_BOARD_PRINCIPLES) >= 8
        assert len(FORBIDDEN_BOARD_ACTIONS) >= 10
        assert "recommendation_recompute" in {a for a, _ in FORBIDDEN_BOARD_ACTIONS}

    def test_fix_175_composes_upstream_without_duplication(self) -> None:
        _gate_review_stack(SESSION)
        append_governed_lane_entry_recommendation_record(
            session_id=SESSION,
            kind="lane_recommendation_artifact",
            content="Recommendation for board composition test.",
        )
        result = build_governed_lane_readiness_board(session_id=SESSION)
        assert result.ok is True
        board = result.governed_lane_readiness_board

        assert set(board["fix_175_certification_requirements"]) == set(FIX_175_CERTIFICATION_REQUIREMENTS)
        assert board["composes_upstream_layers_not_duplicates"] is True
        assert board["sources"]["composes_governed_lane_entry_recommendation"] is True

        section_keys = set(board.get("sections") or {})
        assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_174)

        rec_read = board["sections"]["lane_recommendation_upstream_read"][0]
        assert rec_read.get("recomputed_by_fix_175") is False

        assert board["lane_admission_decision_performed"] is False
        assert board["lane_admission_performed"] is False
        assert "board" in GOVERNED_LANE_READINESS_BOARD_INVARIANT.lower()

    def test_governed_lane_readiness_board_cognition_layer(self) -> None:
        _gate_review_stack(SESSION)
        record, blockers = append_governed_lane_readiness_board_record(
            session_id=SESSION,
            kind="lane_readiness_board_artifact",
            content="Board artifact for human admission prep.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False
        assert record.get("lane_admission_decision_performed") is False

        result = build_governed_lane_readiness_board(session_id=SESSION)
        assert result.ok is True
        assert result.governed_lane_readiness_board["governed_lane_readiness_board_cognition"] is True

    def test_operator_api_includes_governed_lane_readiness_board_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/governed-lane-readiness-board" in paths
        assert "/mission-control/governed-lane-readiness-board/record" in paths
