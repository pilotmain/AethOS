# SPDX-License-Identifier: Apache-2.0
"""FIX 173 — gate-routed package outcome review certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_173_CERTIFICATION_REQUIREMENTS
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
from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_173,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_173,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_173,
    CODE_WRITE_ENABLED_FIX_173,
    EXECUTION_PERFORMED_FIX_173,
    FORBIDDEN_REVIEW_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_173,
    GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_FIX,
    GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_INVARIANT,
    GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_PRINCIPLES,
    GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_SCHEMA_VERSION,
    GOVERNANCE_MUTATION_PERFORMED_FIX_173,
    MERGE_DEPLOY_ENABLED_FIX_173,
    MUTATION_PERFORMED_FIX_173,
    PR_ACTION_ENABLED_FIX_173,
    RAILWAY_MUTATION_ENABLED_FIX_173,
    TIER_ESCALATION_ENABLED_FIX_173,
)
from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_service import (
    build_gate_routed_package_outcome_review,
)
from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_store import (
    append_gate_routed_package_outcome_review_record,
    clear_gate_routed_package_outcome_review_records_for_tests,
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

SESSION = "mc-gtrev-cert-173"


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
    clear_gate_routed_package_outcome_review_records_for_tests()
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


class TestMissionControlGateRoutedPackageOutcomeReviewCertification:
    def test_fix_173_contract(self) -> None:
        assert GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_FIX == "FIX 173"
        assert GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_SCHEMA_VERSION == (
            "mission_control_gate_routed_package_outcome_review_v1"
        )
        assert MUTATION_PERFORMED_FIX_173 is False
        assert EXECUTION_PERFORMED_FIX_173 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_173 is False
        assert AUTONOMOUS_EXECUTION_ENABLED_FIX_173 is False
        assert AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_173 is False
        assert TIER_ESCALATION_ENABLED_FIX_173 is False
        assert GATE_BYPASS_ENABLED_FIX_173 is False
        assert CODE_WRITE_ENABLED_FIX_173 is False
        assert PR_ACTION_ENABLED_FIX_173 is False
        assert MERGE_DEPLOY_ENABLED_FIX_173 is False
        assert RAILWAY_MUTATION_ENABLED_FIX_173 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_173 is False
        assert len(GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_PRINCIPLES) >= 8
        assert len(FORBIDDEN_REVIEW_ACTIONS) >= 7

    def test_fix_173_governance_friction_certification_requirements(self) -> None:
        _full_stack(SESSION)
        append_human_decision_board_record(
            session_id=SESSION,
            kind="selection_record",
            content="governed_delivery_continuation",
        )
        append_execution_handoff_coordination_record(
            session_id=SESSION,
            kind="handoff_artifact",
            content="Handoff for gate review.",
        )
        append_bounded_delivery_work_packages_record(
            session_id=SESSION,
            kind="work_package_artifact",
            content="Work packages for gate review.",
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
        append_governed_task_execution_coordination_record(
            session_id=SESSION,
            kind="coordination_artifact",
            content="Coordinate before gate review.",
        )
        result = build_gate_routed_package_outcome_review(session_id=SESSION)
        assert result.ok is True
        review = result.gate_routed_package_outcome_review

        assert set(review["fix_173_certification_requirements"]) == set(FIX_173_CERTIFICATION_REQUIREMENTS)
        assert review["review_ready"] is True
        assert review["execution_performed"] is False

        for row in review["sections"]["frozen_gate_mapping"]:
            assert row.get("gate_bypass") is not True

        for row in review["sections"]["gate_handler_routing"]:
            assert row.get("gate_bypass") is not True

        assert review["autonomous_lane_entry_enabled"] is False
        assert review["gate_bypass_enabled"] is False
        assert "review" in GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_INVARIANT.lower()

    def test_gate_routed_package_outcome_review_cognition_layer(self) -> None:
        _full_stack(SESSION)
        append_human_decision_board_record(
            session_id=SESSION,
            kind="selection_record",
            content="governed_delivery_continuation",
        )
        record, blockers = append_gate_routed_package_outcome_review_record(
            session_id=SESSION,
            kind="gate_review_artifact",
            content="Review outcomes without lane entry.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False

        result = build_gate_routed_package_outcome_review(session_id=SESSION)
        assert result.ok is True
        assert result.gate_routed_package_outcome_review["gate_routed_package_outcome_review_cognition"] is True
        assert result.gate_routed_package_outcome_review["gate_review_record_count"] == 1

    def test_operator_api_includes_gate_routed_package_outcome_review_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/gate-routed-package-outcome-review" in paths
        assert "/mission-control/gate-routed-package-outcome-review/record" in paths
