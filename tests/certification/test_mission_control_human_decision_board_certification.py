# SPDX-License-Identifier: Apache-2.0
"""FIX 166 — human decision board certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.human_decision_board.human_decision_board_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_166,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_166,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_166,
    AUTONOMOUS_MERGE_ENABLED_FIX_166,
    AUTONOMOUS_PR_CREATION_ENABLED_FIX_166,
    AUTONOMOUS_RAILWAY_MUTATION_ENABLED_FIX_166,
    AUTONOMOUS_SELECTION_ENABLED_FIX_166,
    DECISION_BOARD_EXECUTABLE,
    DECISION_PRINCIPLES,
    DECISION_RECORD_KINDS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_166,
    HUMAN_DECISION_BOARD_FIX,
    HUMAN_DECISION_BOARD_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_166,
)
from aethos_core.mission_control.human_decision_board.human_decision_board_service import build_human_decision_board
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

SESSION = "mc-decision-cert-166"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_human_decision_board_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_human_decision_board_records_for_tests()


class TestMissionControlHumanDecisionBoardCertification:
    def test_fix_166_contract(self) -> None:
        assert HUMAN_DECISION_BOARD_FIX == "FIX 166"
        assert HUMAN_DECISION_BOARD_SCHEMA_VERSION == "mission_control_human_decision_board_v1"
        assert MUTATION_PERFORMED_FIX_166 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_166 is False
        assert AUTONOMOUS_SELECTION_ENABLED_FIX_166 is False
        assert AUTONOMOUS_EXECUTION_ENABLED_FIX_166 is False
        assert AUTONOMOUS_APPROVAL_ENABLED_FIX_166 is False
        assert AUTONOMOUS_PR_CREATION_ENABLED_FIX_166 is False
        assert AUTONOMOUS_MERGE_ENABLED_FIX_166 is False
        assert AUTONOMOUS_RAILWAY_MUTATION_ENABLED_FIX_166 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_166 is False
        assert DECISION_BOARD_EXECUTABLE is False
        assert "selection_record" in DECISION_RECORD_KINDS
        assert len(DECISION_PRINCIPLES) >= 8

    def test_human_decision_board_cognition_layer(self) -> None:
        _full_stack(SESSION)
        record, blockers = append_human_decision_board_record(
            session_id=SESSION,
            kind="selection_record",
            content="Advisory human selection: hold_no_go_path until deliberation complete.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False
        assert record["autonomous_selection"] is False

        result = build_human_decision_board(session_id=SESSION)
        assert result.ok is True
        assert result.human_decision_board["human_decision_board_cognition"] is True
        assert result.human_decision_board["human_selection_cognition"] is True
        assert result.human_decision_board["decision_record_count"] == 1

    def test_operator_api_includes_human_decision_board_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/human-decision-board" in paths
        assert "/mission-control/human-decision-board/record" in paths
