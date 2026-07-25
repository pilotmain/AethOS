# SPDX-License-Identifier: Apache-2.0
"""FIX 164 — mission planning certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.mission_planning.mission_planning_contract import (
    ACTION_OPTION_CATALOG,
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_164,
    AUTONOMOUS_ACTION_EXECUTION_ENABLED_FIX_164,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_164,
    AUTO_PATH_SELECTION_ENABLED_FIX_164,
    DO_NOT_DO_CATALOG,
    GOVERNANCE_MUTATION_PERFORMED_FIX_164,
    MERGE_DEPLOY_RESTART_ENABLED_FIX_164,
    MISSION_PLANNING_FIX,
    MISSION_PLANNING_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_164,
    PLANNING_PRINCIPLES,
    PLANNING_RECOMMENDATION_EXECUTABLE,
    PLANNING_RECORD_KINDS,
    PR_OPEN_ENABLED_FIX_164,
    RAILWAY_MUTATION_ENABLED_FIX_164,
)
from aethos_core.mission_control.mission_planning.mission_planning_service import build_mission_planning
from aethos_core.mission_control.mission_planning.mission_planning_store import (
    append_mission_planning_record,
    clear_mission_planning_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-planning-cert-164"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_mission_planning_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_mission_planning_records_for_tests()


class TestMissionControlMissionPlanningCertification:
    def test_fix_164_contract(self) -> None:
        assert MISSION_PLANNING_FIX == "FIX 164"
        assert MISSION_PLANNING_SCHEMA_VERSION == "mission_control_mission_planning_v1"
        assert MUTATION_PERFORMED_FIX_164 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_164 is False
        assert AUTONOMOUS_ACTION_EXECUTION_ENABLED_FIX_164 is False
        assert AUTONOMOUS_APPROVAL_ENABLED_FIX_164 is False
        assert AUTO_PATH_SELECTION_ENABLED_FIX_164 is False
        assert RAILWAY_MUTATION_ENABLED_FIX_164 is False
        assert PR_OPEN_ENABLED_FIX_164 is False
        assert MERGE_DEPLOY_RESTART_ENABLED_FIX_164 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_164 is False
        assert PLANNING_RECOMMENDATION_EXECUTABLE is False
        assert "action_option_note" in PLANNING_RECORD_KINDS
        assert len(PLANNING_PRINCIPLES) >= 8
        assert len(ACTION_OPTION_CATALOG) >= 4
        assert len(DO_NOT_DO_CATALOG) >= 4

    def test_mission_planning_cognition_layer(self) -> None:
        _full_stack(SESSION)
        record, blockers = append_mission_planning_record(
            session_id=SESSION,
            kind="action_option_note",
            content="Advisory: compare institutional action options before human lane selection.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False

        result = build_mission_planning(session_id=SESSION)
        assert result.ok is True
        assert result.mission_planning["mission_planning_cognition"] is True
        assert result.mission_planning["institutional_action_cognition"] is True
        assert result.mission_planning["planning_record_count"] == 1

    def test_operator_api_includes_mission_planning_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/mission-planning" in paths
        assert "/mission-control/mission-planning/record" in paths
