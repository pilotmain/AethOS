# SPDX-License-Identifier: Apache-2.0
"""FIX 171 — bounded execution participation certification (governance friction contract)."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_171_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_171,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_171,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_171,
    BOUNDED_EXECUTION_PARTICIPATION_EXECUTABLE,
    BOUNDED_EXECUTION_PARTICIPATION_FIX,
    BOUNDED_EXECUTION_PARTICIPATION_INVARIANT,
    BOUNDED_EXECUTION_PARTICIPATION_PRINCIPLES,
    BOUNDED_EXECUTION_PARTICIPATION_SCHEMA_VERSION,
    FORBIDDEN_PARTICIPATION_ACTIONS,
    FORBIDDEN_PARTICIPATION_LANES,
    GATE_BYPASS_ENABLED_FIX_171,
    GOVERNANCE_MUTATION_PERFORMED_FIX_171,
    MERGE_DEPLOY_ENABLED_FIX_171,
    MUTATION_PERFORMED_FIX_171,
    PR_OPEN_ENABLED_FIX_171,
    RAILWAY_MUTATION_ENABLED_FIX_171,
    TIER_ESCALATION_ENABLED_FIX_171,
)
from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_service import (
    build_bounded_execution_participation,
)
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

SESSION = "mc-bepart-cert-171"


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
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_human_decision_board_records_for_tests()
    clear_execution_handoff_coordination_records_for_tests()
    clear_bounded_delivery_work_packages_records_for_tests()
    clear_mission_authorization_records_for_tests()
    clear_bounded_execution_participation_records_for_tests()


class TestMissionControlBoundedExecutionParticipationCertification:
    def test_fix_171_contract(self) -> None:
        assert BOUNDED_EXECUTION_PARTICIPATION_FIX == "FIX 171"
        assert BOUNDED_EXECUTION_PARTICIPATION_SCHEMA_VERSION == "mission_control_bounded_execution_participation_v1"
        assert MUTATION_PERFORMED_FIX_171 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_171 is False
        assert AUTONOMOUS_EXECUTION_ENABLED_FIX_171 is False
        assert AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_171 is False
        assert TIER_ESCALATION_ENABLED_FIX_171 is False
        assert GATE_BYPASS_ENABLED_FIX_171 is False
        assert PR_OPEN_ENABLED_FIX_171 is False
        assert MERGE_DEPLOY_ENABLED_FIX_171 is False
        assert RAILWAY_MUTATION_ENABLED_FIX_171 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_171 is False
        assert BOUNDED_EXECUTION_PARTICIPATION_EXECUTABLE is False
        assert "railway_orchestration" in FORBIDDEN_PARTICIPATION_LANES
        assert len(BOUNDED_EXECUTION_PARTICIPATION_PRINCIPLES) >= 8
        assert len(FORBIDDEN_PARTICIPATION_ACTIONS) >= 7

    def test_fix_171_governance_friction_certification_requirements(self) -> None:
        _full_stack(SESSION)
        append_human_decision_board_record(
            session_id=SESSION,
            kind="selection_record",
            content="governed_delivery_continuation",
        )
        append_execution_handoff_coordination_record(
            session_id=SESSION,
            kind="handoff_artifact",
            content="Handoff for bounded execution participation.",
        )
        append_bounded_delivery_work_packages_record(
            session_id=SESSION,
            kind="work_package_artifact",
            content="Work packages for participation.",
        )
        append_mission_authorization_record(
            session_id=SESSION,
            kind="mission_authorization_artifact",
            content="Bounded Tier 1-2 envelope.",
        )
        result = build_bounded_execution_participation(session_id=SESSION)
        assert result.ok is True
        participation = result.bounded_execution_participation

        assert set(participation["fix_171_certification_requirements"]) == set(FIX_171_CERTIFICATION_REQUIREMENTS)

        scope = next(
            row
            for row in participation["sections"]["participation_scope"]
            if row.get("scope_id") == "envelope-participation-scope"
        )
        allowed = set(scope.get("allowed_lanes") or [])
        assert "software_delivery" in allowed
        assert not allowed.intersection(set(FORBIDDEN_PARTICIPATION_LANES))
        assert scope.get("autonomous_lane_entry") is False

        tier = participation["sections"]["tier_boundary_enforcement"][0]
        assert tier.get("tier_3_4_satisfied") is False

        for row in participation["sections"]["gate_routed_participation"]:
            assert row.get("gate_bypass") is not True
            assert row.get("approval_bypass") is not True

        assert participation["autonomous_lane_entry_enabled"] is False
        assert participation["gate_bypass_enabled"] is False
        assert participation["merge_deploy_enabled"] is False
        assert "envelope" in BOUNDED_EXECUTION_PARTICIPATION_INVARIANT.lower()

    def test_bounded_execution_participation_cognition_layer(self) -> None:
        _full_stack(SESSION)
        append_human_decision_board_record(
            session_id=SESSION,
            kind="selection_record",
            content="governed_delivery_continuation",
        )
        record, blockers = append_bounded_execution_participation_record(
            session_id=SESSION,
            kind="participation_artifact",
            content="Agent participation within authorized envelope.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False

        result = build_bounded_execution_participation(session_id=SESSION)
        assert result.ok is True
        assert result.bounded_execution_participation["bounded_execution_participation_cognition"] is True
        assert result.bounded_execution_participation["participation_record_count"] == 1

    def test_operator_api_includes_bounded_execution_participation_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/bounded-execution-participation" in paths
        assert "/mission-control/bounded-execution-participation/record" in paths
