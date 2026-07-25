# SPDX-License-Identifier: Apache-2.0
"""FIX 165 — mission planning deliberation certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_165,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_165,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_165,
    AUTONOMOUS_LANE_SELECTION_ENABLED_FIX_165,
    AUTONOMOUS_MERGE_ENABLED_FIX_165,
    AUTONOMOUS_PR_CREATION_ENABLED_FIX_165,
    AUTONOMOUS_RAILWAY_MUTATION_ENABLED_FIX_165,
    BOUNDED_DELIBERATION_AGENT_ROLE_IDS,
    DELIBERATION_AGENT_CATALOG,
    DELIBERATION_PRINCIPLES,
    DELIBERATION_RECOMMENDATION_EXECUTABLE,
    DELIBERATION_RECORD_KINDS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_165,
    MISSION_PLANNING_DELIBERATION_FIX,
    MISSION_PLANNING_DELIBERATION_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_165,
)
from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_service import (
    build_mission_planning_deliberation,
)
from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_store import (
    append_mission_planning_deliberation_record,
    clear_mission_planning_deliberation_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-deliberation-cert-165"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_mission_planning_deliberation_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_mission_planning_deliberation_records_for_tests()


class TestMissionControlMissionPlanningDeliberationCertification:
    def test_fix_165_contract(self) -> None:
        assert MISSION_PLANNING_DELIBERATION_FIX == "FIX 165"
        assert MISSION_PLANNING_DELIBERATION_SCHEMA_VERSION == "mission_control_mission_planning_deliberation_v1"
        assert MUTATION_PERFORMED_FIX_165 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_165 is False
        assert AUTONOMOUS_EXECUTION_ENABLED_FIX_165 is False
        assert AUTONOMOUS_APPROVAL_ENABLED_FIX_165 is False
        assert AUTONOMOUS_LANE_SELECTION_ENABLED_FIX_165 is False
        assert AUTONOMOUS_PR_CREATION_ENABLED_FIX_165 is False
        assert AUTONOMOUS_RAILWAY_MUTATION_ENABLED_FIX_165 is False
        assert AUTONOMOUS_MERGE_ENABLED_FIX_165 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_165 is False
        assert DELIBERATION_RECOMMENDATION_EXECUTABLE is False
        assert "planner_analysis_note" in DELIBERATION_RECORD_KINDS
        assert len(DELIBERATION_PRINCIPLES) >= 8
        assert len(BOUNDED_DELIBERATION_AGENT_ROLE_IDS) == 6
        assert len(DELIBERATION_AGENT_CATALOG) == 6

    def test_mission_planning_deliberation_cognition_layer(self) -> None:
        _full_stack(SESSION)
        record, blockers = append_mission_planning_deliberation_record(
            session_id=SESSION,
            kind="planner_analysis_note",
            content="Advisory: bounded agents analyze institutional paths without execution authority.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False

        result = build_mission_planning_deliberation(session_id=SESSION)
        assert result.ok is True
        assert result.mission_planning_deliberation["mission_planning_deliberation_cognition"] is True
        assert result.mission_planning_deliberation["bounded_multi_agent_deliberation"] is True
        assert result.mission_planning_deliberation["deliberation_record_count"] == 1
        assert result.mission_planning_deliberation["agent_role_count"] == 6

    def test_operator_api_includes_mission_planning_deliberation_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/mission-planning-deliberation" in paths
        assert "/mission-control/mission-planning-deliberation/record" in paths
